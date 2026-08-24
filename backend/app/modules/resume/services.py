import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.modules.match.services import _extract_skills


def _summarize_resume(raw_text: str) -> dict:
    """从简历文本提取结构化摘要，供匹配和展示使用"""
    section_names = ["教育", "项目", "经验", "技能", "经历", "自我评价"]
    sections = [name for name in section_names if name in (raw_text or "")]
    return {
        "sections": sections,
        "skills": sorted(_extract_skills(raw_text or "")),
        "has_contact": bool(
            re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw_text or "")
            or re.search(r"1[3-9]\d{9}", raw_text or "")
        ),
    }


def list_resumes(db: Session, user_id: str) -> list:
    """获取当前用户的简历列表"""
    return db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(Resume.created_at.desc()).all()


def get_resume_versions(resume_id: str, db: Session, user_id: str):
    """获取简历版本历史：单用户 MVP 中所有版本属于同一份简历文档"""
    doc = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    if not doc:
        return None
    return db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(Resume.version.desc()).all()


def upload_resume(
    raw_text: str,
    source_file: Optional[str],
    db: Session,
    user_id: str
) -> Resume:
    """上传并保存简历"""
    latest = db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(Resume.version.desc()).first()

    next_version = (latest.version + 1) if latest else 1

    resume = Resume(
        user_id=user_id,
        version=next_version,
        raw_text=raw_text,
        parsed_json=_summarize_resume(raw_text),
        source_file=source_file,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def save_optimized_version(
    resume_id: str,
    optimized_text: str,
    changes: list,
    db: Session,
    user_id: str
) -> Resume:
    """把优化结果保存为简历新版本"""
    source = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
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
        },
        source_file="optimized",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume