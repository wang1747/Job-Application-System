import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import get_settings
from app.models.interview import InterviewArticle, InterviewQuestion, InterviewSession
from app.models.resume import Resume
from app.models.jd import JobDescription
from app.agents.graphs.mock_interview import (
    generate_question,
    evaluate_answer,
    generate_interview_summary,
)

logger = logging.getLogger(__name__)

_ARTICLE_SORT_FIELDS = {"created_at", "company", "position"}


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

    if sort_by not in _ARTICLE_SORT_FIELDS:
        sort_by = "created_at"
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"

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
    db.query(InterviewQuestion).filter(
        InterviewQuestion.article_id == article_id,
        InterviewQuestion.user_id == settings.default_user_id
    ).delete(synchronize_session=False)
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
    return []


def save_generated_questions(
    user_id: str,
    article_id: Optional[str],
    questions: list,
    db: Session
) -> list:
    """持久化生成的面试题"""
    saved = []
    for item in questions:
        question = InterviewQuestion(
            user_id=user_id,
            article_id=article_id,
            question=item["question"],
            category=item.get("category"),
            difficulty=item.get("difficulty"),
        )
        db.add(question)
        saved.append(question)
    db.commit()
    return saved


# ============ 模拟面试会话功能 ============

def create_interview_session(
    resume_id: str,
    jd_id: str,
    db: Session
) -> InterviewSession:
    """创建模拟面试会话"""
    settings = get_settings()
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == settings.default_user_id
    ).first()
    if not resume:
        raise ValueError("简历不存在")
    
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == settings.default_user_id
    ).first()
    if not jd:
        raise ValueError("JD不存在")
    
    session = InterviewSession(
        user_id=settings.default_user_id,
        resume_id=resume_id,
        jd_id=jd_id,
        status="active",
        questions=[],
        answers=[],
        feedbacks=[],
        current_question=""
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    first_question = generate_question(
        resume_text=resume.raw_text,
        jd_text=jd.raw_text
    )
    session.current_question = first_question
    session.questions = [first_question]
    db.commit()
    
    return session


def get_interview_session(session_id: str, db: Session) -> Optional[InterviewSession]:
    """获取会话"""
    settings = get_settings()
    return db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == settings.default_user_id
    ).first()


def submit_interview_answer(
    session_id: str,
    answer: str,
    db: Session
) -> Tuple[Optional[str], Optional[str], bool]:
    """
    提交回答，返回反馈和下一题
    """
    settings = get_settings()
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == settings.default_user_id
    ).first()
    
    if not session:
        return None, None, False
    
    if session.status == "finished":
        return None, None, True
    
    resume = db.query(Resume).filter(
        Resume.id == session.resume_id,
        Resume.user_id == settings.default_user_id
    ).first()
    jd = db.query(JobDescription).filter(
        JobDescription.id == session.jd_id,
        JobDescription.user_id == settings.default_user_id
    ).first()
    if not resume or not jd:
        raise ValueError("会话关联的简历或JD不存在")
    
    current_answers = list(session.answers or [])
    current_answers.append(answer)
    session.answers = current_answers
    
    feedback = evaluate_answer(
        question=session.current_question,
        answer=answer
    )
    current_feedbacks = list(session.feedbacks or [])
    current_feedbacks.append(feedback)
    session.feedbacks = current_feedbacks
    
    question_count = len(session.questions or [])
    if question_count >= 8:
        session.status = "finished"
        db.commit()
        return feedback, None, True
    
    next_question = generate_question(
        resume_text=resume.raw_text,
        jd_text=jd.raw_text,
        previous_question=session.current_question,
        previous_answer=answer
    )
    current_questions = list(session.questions or [])
    current_questions.append(next_question)
    session.questions = current_questions
    session.current_question = next_question
    
    db.commit()
    return feedback, next_question, False


def get_interview_summary(session_id: str, db: Session) -> Optional[dict]:
    """获取面试总结"""
    session = get_interview_session(session_id, db)
    if not session:
        return None
    
    summary_text = ""
    if session.answers:
        summary_text = generate_interview_summary(
            questions=session.questions or [],
            answers=session.answers or [],
            feedbacks=session.feedbacks or [],
        )

    return {
        "summary": summary_text,
        "total_questions": len(session.questions or []),
        "questions": session.questions,
        "answers": session.answers,
        "feedbacks": session.feedbacks,
        "status": session.status,
        "created_at": session.created_at
    }
