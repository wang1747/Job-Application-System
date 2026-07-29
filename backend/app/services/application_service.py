from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.application import Application, ApplicationEvent


def create_application(company: str, position: str, jd_id: Optional[str], resume_id: Optional[str], db: Session) -> Application:
    """创建投递记录"""
    settings = get_settings()
    app = Application(
        user_id=settings.default_user_id,
        company=company,
        position=position,
        jd_id=jd_id,
        resume_id=resume_id,
        status="saved",
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def list_applications(db: Session) -> list:
    """获取投递列表"""
    settings = get_settings()
    return db.query(Application).filter(
        Application.user_id == settings.default_user_id
    ).order_by(Application.updated_at.desc()).all()


def add_event(application_id: str, event_type: str, from_status: Optional[str], to_status: Optional[str], description: Optional[str], db: Session) -> Optional[ApplicationEvent]:
    """添加投递事件"""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        return None
    event = ApplicationEvent(
        application_id=application_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        description=description,
        event_date=datetime.now(),
    )
    if to_status:
        app.status = to_status
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
