from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.interview import InterviewArticle, InterviewQuestion


def import_article(company: str, position: Optional[str], raw_content: str, source: str, db: Session) -> InterviewArticle:
    """导入面经文章"""
    settings = get_settings()
    article = InterviewArticle(
        user_id=settings.default_user_id,
        company=company,
        position=position,
        raw_content=raw_content,
        source=source,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_questions(db: Session) -> list:
    """获取面试题列表"""
    settings = get_settings()
    return db.query(InterviewQuestion).filter(
        InterviewQuestion.user_id == settings.default_user_id
    ).all()
