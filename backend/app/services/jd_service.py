from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.jd import JobDescription
from app.agents.graphs.jd_analysis import analyze_jd


async def parse_and_save(raw_text: str, db: Session) -> dict:
    settings = get_settings()
    result = await analyze_jd(raw_text)
    if result.get("error"):
        return {"success": False, "data": None, "error": result["error"]}

    parsed = result.get("parsed", {})
    jd = JobDescription(
        user_id=settings.default_user_id,
        raw_text=raw_text,
        company=parsed.get("company"),
        position=parsed.get("position"),
        must_have=parsed.get("must_have"),
        nice_to_have=parsed.get("nice_to_have"),
        tech_stack=parsed.get("tech_stack"),
        hidden_signals=parsed.get("hidden_signals"),
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return {"success": True, "data": {"id": jd.id, "parsed": parsed}, "error": None}


def list_jds(db: Session) -> list:
    settings = get_settings()
    return db.query(JobDescription).filter(
        JobDescription.user_id == settings.default_user_id
    ).order_by(JobDescription.created_at.desc()).all()


def delete_jd(jd_id: str, db: Session) -> bool:
    settings = get_settings()
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == settings.default_user_id
    ).first()
    if not jd:
        return False
    db.delete(jd)
    db.commit()
    return True
