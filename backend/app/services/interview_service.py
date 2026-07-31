from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import get_settings
from app.models.interview import InterviewArticle, InterviewQuestion


def import_article(
    company: str,
    raw_content: str,
    db: Session,
    position: Optional[str] = None,
    source: str = "manual"
) -> InterviewArticle:
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


def list_articles(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    company: Optional[str] = None,
    position: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[list, int]:
    """获取面经列表（带分页和筛选）"""
    settings = get_settings()
    query = db.query(InterviewArticle).filter(
        InterviewArticle.user_id == settings.default_user_id
    )

    if company:
        query = query.filter(InterviewArticle.company.ilike(f"%{company}%"))
    if position:
        query = query.filter(InterviewArticle.position.ilike(f"%{position}%"))

    # 排序
    if sort_order == "desc":
        query = query.order_by(desc(getattr(InterviewArticle, sort_by)))
    else:
        query = query.order_by(getattr(InterviewArticle, sort_by))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def delete_article(article_id: str, db: Session) -> bool:
    """删除面经"""
    settings = get_settings()
    article = db.query(InterviewArticle).filter(
        InterviewArticle.id == article_id,
        InterviewArticle.user_id == settings.default_user_id
    ).first()
    if not article:
        return False
    db.delete(article)
    db.commit()
    return True


def get_questions(
    db: Session,
    article_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[list, int]:
    """获取面试题列表（支持按面经筛选）"""
    settings = get_settings()
    query = db.query(InterviewQuestion).filter(
        InterviewQuestion.user_id == settings.default_user_id
    )

    if article_id:
        query = query.filter(InterviewQuestion.article_id == article_id)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def extract_questions_from_article(article_id: str, db: Session) -> list:
    """从面经中提取题目（占位，后续接入LLM）"""
    # TODO: 接入 LangGraph 面试题提取工作流
    return []