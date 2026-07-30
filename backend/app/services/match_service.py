from typing import Optional
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.match import MatchResult


def calculate_match(jd_id: str, resume_id: str, db: Session) -> dict:
    """
    计算 JD 与简历的匹配度（占位）
    后续接入 LangGraph 匹配工作流 + ChromaDB 语义匹配
    """
    # 生成模拟匹配数据
    import random
    score = random.randint(60, 95)
    return {
        "score": score,
        "skill_match_detail": {
            "matched": ["Python", "Django", "MySQL"],
            "missing": ["高并发", "Docker"],
            "partial": ["微服务"]
        },
        "gap_analysis": {
            "hard_gap": ["高并发经验", "Docker/K8s"],
            "soft_gap": [],
            "suggestion": "建议补充高并发和容器化相关项目经验"
        },
        "suggestion": "建议针对缺失技能进行补充学习，可参考JD中的硬性要求"
    }


def get_rankings(db: Session) -> list:
    """
    获取按匹配度排序的 JD 列表（占位）
    后续接入真实匹配逻辑
    """
    settings = get_settings()
    # 查询已有的匹配结果，按分数降序
    return db.query(MatchResult).filter(
        MatchResult.jd_id.isnot(None)
    ).order_by(MatchResult.score.desc()).all()