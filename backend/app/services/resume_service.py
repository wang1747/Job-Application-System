from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.resume import Resume


def list_resumes(db: Session) -> list:
    """获取当前用户的简历列表"""
    settings = get_settings()
    return db.query(Resume).filter(
        Resume.user_id == settings.default_user_id
    ).order_by(Resume.created_at.desc()).all()


def get_resume_versions(resume_id: str, db: Session) -> list:
    """获取简历版本历史"""
    settings = get_settings()
    return db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == settings.default_user_id
    ).order_by(Resume.version.desc()).all()
