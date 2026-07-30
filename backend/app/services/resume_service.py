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
    """获取简历版本历史（当前模型无group_id，暂无法实现多版本分组）"""
    settings = get_settings()
    return db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == settings.default_user_id
    ).order_by(Resume.version.desc()).all()


def upload_resume(
    raw_text: str,
    source_file: Optional[str],
    db: Session
) -> Resume:
    """上传并保存简历"""
    settings = get_settings()
    
    # 获取当前最大版本号
    latest = db.query(Resume).filter(
        Resume.user_id == settings.default_user_id
    ).order_by(Resume.version.desc()).first()
    
    next_version = (latest.version + 1) if latest else 1
    
    resume = Resume(
        user_id=settings.default_user_id,
        version=next_version,
        raw_text=raw_text,
        source_file=source_file,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume