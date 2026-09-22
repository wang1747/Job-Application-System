from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.skill_keywords import directions as skill_directions, top_keywords
from app.models.jd import JobDescription
from app.models.resume import Resume
from app.models.user import User
from app.modules.auth.routes import get_current_user_required
from app.modules.resume.services import upload_resume

from .contracts import GenerationResult
from .schemas import (
    RegenerateSectionRequest,
    ResumeGenerateRequest,
    SaveStructuredRequest,
)
from .services import (
    generate_resume,
    regenerate_section,
    regenerate_section_variants,
    save_structured,
)

router = APIRouter()


@router.get("/recommend-skills")
async def recommend_skills(
    direction: str = "",
    limit: int = 12,
    current_user: User = Depends(get_current_user_required),
):
    """按岗位方向返回真实 JD 词频 top N 推荐技能。

    - 不带 direction：返回所有方向及其 top N 技能
    - 带 direction（如「Java开发」）：返回该方向的 top N 技能
    """
    limit = max(1, min(limit, 30))
    if direction:
        return {
            "success": True,
            "data": {"direction": direction, "skills": top_keywords(direction, limit)},
            "error": None,
        }
    all_skills = {d: top_keywords(d, limit) for d in skill_directions()}
    return {"success": True, "data": {"directions": all_skills}, "error": None}


def _structured_dict(result: GenerationResult) -> dict:
    return {
        "name": result.name,
        "position": result.position,
        "contact": result.contact,
        "summary": result.summary,
        "education": result.education,
        "experiences": result.experiences,
        "skills": result.skills,
        "certifications": result.certifications,
    }


def _result_data(resume: Resume, result: GenerationResult) -> dict:
    return {
        "id": resume.id,
        "version": resume.version,
        "resume_text": result.resume_text,
        "name": result.name,
        "position": result.position,
        "contact": result.contact,
        "summary": result.summary,
        "education": result.education,
        "experiences": result.experiences,
        "skills": result.skills,
        "certifications": result.certifications,
        "sections": result.sections,
        "tips": result.tips,
        "risks": result.risks,
        "jd_alignment": result.jd_alignment,
        "reference_source": result.reference_source,
        "ats": result.ats,
        "gap": result.gap,
        "fidelity": result.fidelity,
    }


def _load_jd(jd_id: str | None, db: Session, user_id: str):
    if not jd_id:
        return None
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == user_id,
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="目标岗位不存在")
    return jd


@router.post("/generate")
async def generate_resume_endpoint(
    req: ResumeGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    jd = _load_jd(req.jd_id, db, current_user.id)
    result = await generate_resume(req, current_user, jd=jd)
    if result.error:
        return {"success": False, "data": None, "error": result.error}

    try:
        resume = upload_resume(
            raw_text=result.resume_text,
            source_file="AI 生成",
            db=db,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    resume.parsed_json = {
        **(resume.parsed_json or {}),
        "structured": _structured_dict(result),
        "generation": _result_data(resume, result),
        "kind": "generated",
    }
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 贡献语料：用户同意才把生成的简历写入共享语料库（默认关闭）
    if current_user.allow_corpus:
        try:
            from app.modules.corpus.services import add_corpus_item
            add_corpus_item(
                item_type="resume",
                raw_text=resume.raw_text,
                db=db,
                structured={"structured": _structured_dict(result)},
                source="user_upload",
                user_id=current_user.id,
                is_public=True,
            )
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] 简历贡献语料失败: {e}")

    return {
        "success": True,
        "data": _result_data(resume, result),
        "error": None,
    }


@router.post("/regenerate-section")
async def regenerate_section_endpoint(
    req: RegenerateSectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    resume = db.query(Resume).filter(
        Resume.id == req.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    jd = _load_jd(req.jd_id, db, current_user.id)
    result = await regenerate_section(
        req.structured,
        req.section,
        req.index,
        req.jd_text or (jd.raw_text if jd else "") or "",
        current_user,
        jd=jd,
    )
    if result.error:
        return {"success": False, "data": None, "error": result.error}

    resume.raw_text = result.resume_text
    resume.parsed_json = {
        **(resume.parsed_json or {}),
        "structured": _structured_dict(result),
        "generation": _result_data(resume, result),
        "kind": "generated",
    }
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "success": True,
        "data": _result_data(resume, result),
        "error": None,
    }


@router.post("/regenerate-section-variants")
async def regenerate_section_variants_endpoint(
    req: RegenerateSectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """为指定字段生成 3 个改写候选，供用户选择（不落库）。"""
    jd = _load_jd(req.jd_id, db, current_user.id)
    candidates = await regenerate_section_variants(
        req.structured,
        req.section,
        req.index,
        req.jd_text or (jd.raw_text if jd else "") or "",
        current_user,
        jd=jd,
    )
    if not candidates:
        return {"success": False, "data": None, "error": "生成候选失败，请重试"}
    return {"success": True, "data": {"candidates": candidates}, "error": None}


@router.post("/save")
async def save_structured_endpoint(
    req: SaveStructuredRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """保存前端选定候选后的完整 structured（不重新调 LLM），并落库。"""
    resume = db.query(Resume).filter(
        Resume.id == req.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    jd = _load_jd(req.jd_id, db, current_user.id)
    result = await save_structured(
        req.structured,
        req.jd_text or (jd.raw_text if jd else "") or "",
        current_user,
        jd=jd,
    )
    if result.error:
        return {"success": False, "data": None, "error": result.error}

    resume.raw_text = result.resume_text
    resume.parsed_json = {
        **(resume.parsed_json or {}),
        "structured": _structured_dict(result),
        "generation": _result_data(resume, result),
        "kind": "generated",
    }
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "success": True,
        "data": _result_data(resume, result),
        "error": None,
    }
