from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.match import MatchResult


def calculate_match(jd_id: str, resume_id: str, db: Session) -> dict:
    """计算 JD 与简历的匹配度（占位）"""
    # TODO: 接入 LangGraph 匹配工作流 + ChromaDB 语义匹配
    return {"score": 0, "skill_match_detail": {}, "gap_analysis": {}, "suggestion": ""}


def get_rankings(db: Session) -> list:
    """获取按匹配度排序的 JD 列表（占位）"""
    settings = get_settings()
    return db.query(MatchResult).filter(
        MatchResult.jd_id.isnot(None)
    ).order_by(MatchResult.score.desc()).all()
