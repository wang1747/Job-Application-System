import re
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.tools.ats_checker import check_ats_compatibility
from app.core.text_utils import extract_skills
from app.models.jd import JobDescription
from app.models.resume import Resume
from app.models.user import User
from app.modules.resume.optimizer import (
    JDRequirement,
    optimize_resume_text,
)


def _summarize_resume(raw_text: str) -> dict:
    """从简历文本提取结构化摘要，供匹配和展示使用。"""
    section_names = ["教育", "项目", "经验", "技能", "经历", "自我评价"]
    sections = [name for name in section_names if name in (raw_text or "")]
    return {
        "sections": sections,
        "skills": sorted(extract_skills(raw_text or "")),
        "has_contact": bool(
            re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw_text or "")
            or re.search(r"1[3-9]\d{9}", raw_text or "")
        ),
    }


def _root_document_id(resume: Resume, by_id: dict) -> str:
    """沿 parent_id 链回溯到根文档（原始简历），把同一份简历的所有版本归为一组。"""
    seen = set()
    current_id = resume.id
    while current_id and current_id not in seen:
        seen.add(current_id)
        item = by_id.get(current_id)
        if not item:
            break
        parent = (item.parsed_json or {}).get("parent_id")
        if not parent:
            return current_id
        current_id = parent
    return resume.id


def list_resumes(db: Session, user_id: str) -> list:
    """获取简历列表。

    个人简历工具的正确心智模型：一份「基础简历」+ 针对不同 JD 的「优化版本」并列展示。
    - 基础简历（原版）：每个独立一条；
    - 优化版本：按目标 JD（公司+职位）分组，同一 JD 反复优化只保留最新；
    - 未记录目标 JD 的早期优化版本：按父简历归为一组。
    """
    all_resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    all_resumes = [r for r in all_resumes if (r.raw_text or "").strip()]

    groups: dict = {}  # key -> [latest_resume, count]
    for r in all_resumes:
        pj = r.parsed_json or {}
        if pj.get("kind") == "optimized":
            tj = pj.get("target_jd") or {}
            company = (tj.get("company") or "").strip()
            position = (tj.get("position") or "").strip()
            if company or position:
                key = ("jd", company, position)
            else:
                key = ("jd_unlabeled", pj.get("parent_id") or "", "")
        else:
            key = ("base", r.id, "")

        if key not in groups:
            groups[key] = (r, 1)
        else:
            prev, count = groups[key]
            groups[key] = (r if r.version > prev.version else prev, count + 1)

    result = []
    for key, (latest, count) in groups.items():
        result.append({
            "id": latest.id,
            "version": latest.version,
            "raw_text": latest.raw_text,
            "source_file": latest.source_file,
            "parsed_json": latest.parsed_json,
            "created_at": latest.created_at,
            "version_count": count,
            "document_id": key[1] or latest.id,
        })
    result.sort(key=lambda x: (x["created_at"] or ""), reverse=True)
    return result


def get_resume_versions(resume_id: str, db: Session, user_id: str):
    """获取同一份简历（同一文档）的所有版本，按版本号倒序。"""
    doc = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id,
    ).first()
    if not doc:
        return None
    all_resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    by_id = {r.id: r for r in all_resumes}
    root = _root_document_id(doc, by_id)
    versions = [r for r in all_resumes if _root_document_id(r, by_id) == root]
    versions.sort(key=lambda r: r.version, reverse=True)
    return versions


def upload_resume(
    raw_text: str,
    source_file: Optional[str],
    db: Session,
    user_id: str,
) -> Resume:
    """上传并保存简历，拒绝空内容。"""
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("简历内容为空，无法上传")

    latest = db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(Resume.version.desc()).first()
    next_version = (latest.version + 1) if latest else 1

    resume = Resume(
        user_id=user_id,
        version=next_version,
        raw_text=text,
        parsed_json=_summarize_resume(text),
        source_file=source_file,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def _build_jd_requirement(jd: Optional[JobDescription], jd_text: str) -> JDRequirement:
    """优先用结构化 JD，否则回退到原始 JD 文本。"""
    if jd is not None:
        tech_stack: list = []
        ts = jd.tech_stack or {}
        if isinstance(ts, dict):
            for values in ts.values():
                if isinstance(values, list):
                    tech_stack.extend(values)
        elif isinstance(ts, list):
            tech_stack = ts

        return JDRequirement(
            raw_text=jd.raw_text or jd_text or "",
            company=jd.company or "",
            position=jd.position or "",
            must_have=jd.must_have or [],
            nice_to_have=jd.nice_to_have or [],
            tech_stack=tech_stack,
            hidden_signals=jd.hidden_signals or [],
        )

    return JDRequirement(raw_text=(jd_text or "").strip())


def save_optimized_version(
    resume_id: str,
    optimized_text: str,
    changes: list,
    target_jd: dict,
    added_keywords: list,
    db: Session,
    user_id: str,
) -> Resume:
    """把优化结果保存为简历新版本，并记录目标 JD 信息。"""
    source = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id,
    ).first()
    if not source:
        raise ValueError("简历不存在")

    latest = db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(Resume.version.desc()).first()
    next_version = (latest.version + 1) if latest else 1

    resume = Resume(
        user_id=user_id,
        version=next_version,
        raw_text=optimized_text,
        parsed_json={
            "kind": "optimized",
            "parent_id": resume_id,
            "changes": changes or [],
            "target_jd": target_jd or {},
            "added_keywords": added_keywords or [],
            "skills": sorted(extract_skills(optimized_text or "")),
        },
        source_file=source.source_file,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


async def optimize_resume_flow(
    resume_id: str,
    jd_text: str,
    db: Session,
    user: User,
    jd_id: Optional[str] = None,
) -> dict:
    """简历优化业务编排：加载原简历 -> 取目标 JD -> 优化 -> 保存新版本。

    支持两种 JD 输入：
    - jd_id：从数据库取结构化 JD（含 must_have/nice_to_have/tech_stack）；
    - jd_text：手动粘贴的 JD 原文。
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user.id,
    ).first()
    if not resume:
        raise ValueError("resume_not_found")

    # 解析目标 JD
    jd: Optional[JobDescription] = None
    if jd_id:
        jd = db.query(JobDescription).filter(
            JobDescription.id == jd_id,
            JobDescription.user_id == user.id,
        ).first()
        if not jd:
            raise ValueError("jd_not_found")
    requirement = _build_jd_requirement(jd, jd_text or "")

    target_jd = {
        "id": jd.id if jd else None,
        "company": requirement.company,
        "position": requirement.position,
    }

    result = await optimize_resume_text(resume.raw_text, requirement, user)
    if result.error:
        return {"success": False, "data": None, "error": result.error}

    new_version = None
    if result.optimized_text and result.optimized_text.strip():
        new_version = save_optimized_version(
            resume_id,
            result.optimized_text,
            [c.__dict__ for c in result.changes],
            target_jd,
            result.added_keywords,
            db,
            user.id,
        )

    return {
        "success": True,
        "data": {
            "optimized": result.optimized_text,
            "changes": [c.__dict__ for c in result.changes],
            "added_keywords": result.added_keywords,
            "removed_keywords": result.removed_keywords,
            "removed": result.removed,
            "length_warning": result.length_warning,
            "gap": {
                "matched": result.gap.matched,
                "missing": result.gap.missing,
                "partial": result.gap.partial,
            },
            "target_jd": target_jd,
            "preservation": {
                "score": result.preservation.score,
                "passed": result.preservation.passed,
                "fallback": result.preservation.fallback,
                "missing_facts": result.preservation.missing_facts,
            },
            "edits_applied": result.edit_count,
            "ats": check_ats_compatibility(resume.raw_text, requirement.raw_text),
            "ats_after": check_ats_compatibility(result.optimized_text, requirement.raw_text),
            "new_version": {
                "id": new_version.id,
                "version": new_version.version,
            } if new_version else None,
        },
        "error": None,
    }
