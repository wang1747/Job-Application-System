"""
面试路由：面经导入、列表、删除、面试题生成、模拟面试
"""

# ===== 标准库 =====
import logging
from typing import Optional, Literal
from datetime import datetime

# ===== 第三方库 =====
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# ===== 项目内部 =====
from app.core.database import get_db
from app.models.resume import Resume
from app.models.jd import JobDescription
from app.models.interview import InterviewArticle
from app.services.interview_service import (
    import_article,
    list_articles,
    delete_article,
    get_questions,
    save_generated_questions,
    extract_article_metadata,
    extract_questions_from_article,
    create_interview_session,
    submit_interview_answer,
    get_interview_summary,
    get_interview_session,
)
from app.agents.graphs.interview_prep import generate_interview_questions
from app.agents.tools.document_parser import parse_article_file
from app.api.routes.auth import get_current_user_required
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/interview", tags=["面试备考模块"])


# ============ 请求/响应模型 ============

class ImportArticleRequest(BaseModel):
    company: str = Field(..., min_length=1, description="公司名称", examples=["字节跳动"])
    position: Optional[str] = Field(None, description="职位", examples=["后端开发"])
    raw_content: str = Field(..., min_length=1, description="面经内容")
    source: str = Field("manual", description="来源")


class GenerateQuestionsRequest(BaseModel):
    resume_id: str = Field(..., description="简历ID")
    jd_id: str = Field(..., description="JD ID")
    article_id: Optional[str] = Field(None, description="面经ID（可选）")
    limit: int = Field(10, ge=1, le=30, description="生成数量上限")


class StartSimulateRequest(BaseModel):
    resume_id: str = Field(..., description="简历ID")
    jd_id: str = Field(..., description="JD ID")


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, description="回答内容")


class ArticleOut(BaseModel):
    id: str
    company: str
    position: Optional[str]
    raw_content: str
    source: str
    questions: Optional[list]
    tags: Optional[list]
    difficulty: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: str
    article_id: Optional[str]
    question: str
    answer: Optional[str]
    category: Optional[str]
    difficulty: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ============ 通用资源查询函数 ============

def _get_resource_or_404(model, resource_id: str, user_id: str, db: Session, resource_name: str):
    """通用资源查询函数"""
    resource = db.query(model).filter(
        model.id == resource_id,
        model.user_id == user_id
    ).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource_name}不存在")
    return resource


# ============ 接口 ============

@router.post(
    "/articles",
    summary="导入面经文章",
    description="导入面经文章，自动去重（相似度 >= 0.9 视为重复），并自动提取题目和标签"
)
async def import_article_endpoint(
    req: ImportArticleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    article, duplicate = import_article(
        company=req.company,
        position=req.position,
        raw_content=req.raw_content,
        source=req.source,
        db=db,
        user_id=current_user.id
    )
    metadata = extract_article_metadata(req.raw_content, user=current_user)
    article.questions = metadata["questions"]
    article.tags = metadata["tags"]
    article.difficulty = metadata["difficulty"]
    db.commit()
    db.refresh(article)
    saved = extract_questions_from_article(article.id, db, current_user.id) if metadata["questions"] else []
    logger.info(f"用户 {current_user.id} 导入面经: {article.id}, duplicate={duplicate}")
    return {
        "success": True,
        "data": {
            "id": article.id,
            "duplicate": duplicate,
            "questions": metadata["questions"],
            "question_count": len(saved),
            "tags": metadata["tags"],
            "difficulty": metadata["difficulty"],
        },
        "error": None,
    }


@router.post(
    "/articles/upload",
    summary="导入面经文件",
    description="上传面经文件（PDF/Markdown/HTML/TXT），自动解析并提取内容"
)
async def upload_article_file(
    file: UploadFile = File(...),
    company: str = File(...),
    position: Optional[str] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    content = await file.read()
    try:
        raw_content = parse_article_file(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    article, duplicate = import_article(
        company=company,
        position=position,
        raw_content=raw_content,
        source="file",
        db=db,
        user_id=current_user.id
    )
    metadata = extract_article_metadata(raw_content, user=current_user)
    article.questions = metadata["questions"]
    article.tags = metadata["tags"]
    article.difficulty = metadata["difficulty"]
    db.commit()
    db.refresh(article)
    saved = extract_questions_from_article(article.id, db, current_user.id) if metadata["questions"] else []
    logger.info(f"用户 {current_user.id} 上传面经文件: {file.filename}, article={article.id}")
    return {
        "success": True,
        "data": {
            "id": article.id,
            "duplicate": duplicate,
            "filename": file.filename,
            "question_count": len(saved),
        },
        "error": None,
    }


@router.get(
    "/articles",
    summary="获取面经列表",
    description="获取面经列表，支持分页、按公司/职位筛选"
)
async def list_articles_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    company: Optional[str] = Query(None, description="公司名称筛选"),
    position: Optional[str] = Query(None, description="职位筛选"),
    sort_by: Literal["created_at", "company", "position"] = Query("created_at", description="排序字段"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="排序方向")
):
    items, total = list_articles(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        company=company,
        position=position,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return {
        "success": True,
        "data": {
            "items": [ArticleOut.model_validate(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        },
        "error": None
    }


@router.delete(
    "/articles/{article_id}",
    summary="删除面经",
    description="删除面经及其关联的所有面试题"
)
async def delete_article_endpoint(
    article_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    if not delete_article(article_id, db, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="面经不存在")
    logger.info(f"用户 {current_user.id} 删除面经: {article_id}")
    return {"success": True, "data": None, "error": None}


@router.get(
    "/questions",
    summary="获取面试题列表",
    description="获取面试题列表，支持按面经筛选和分页"
)
async def get_questions_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
    article_id: Optional[str] = Query(None, description="面经ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    items, total = get_questions(
        db=db,
        user_id=current_user.id,
        article_id=article_id,
        page=page,
        page_size=page_size
    )
    return {
        "success": True,
        "data": {
            "items": [QuestionOut.model_validate(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        },
        "error": None
    }


@router.post(
    "/generate",
    summary="生成面试题",
    description="基于简历 + JD + 面经生成面试题"
)
async def generate_questions_endpoint(
    req: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    # 获取简历
    resume = _get_resource_or_404(Resume, req.resume_id, current_user.id, db, "简历")
    if not resume.raw_text or not resume.raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="简历内容为空")

    # 获取 JD
    jd = _get_resource_or_404(JobDescription, req.jd_id, current_user.id, db, "JD")
    if not jd.raw_text or not jd.raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JD内容为空")

    # 获取面经（可选）
    article_content = ""
    if req.article_id:
        article = _get_resource_or_404(InterviewArticle, req.article_id, current_user.id, db, "面经")
        article_content = article.raw_content or ""
        logger.info(f"用户 {current_user.id} 使用面经: {req.article_id}")

    logger.info(f"用户 {current_user.id} 开始生成面试题: resume={req.resume_id}, jd={req.jd_id}")

    result = await generate_interview_questions(
        resume_text=resume.raw_text,
        jd_text=jd.raw_text,
        user=current_user,
        article_content=article_content,
        limit=req.limit
    )

    if result.get("error"):
        logger.error(f"面试题生成失败: {result.get('error')}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])

    questions = result.get("questions", [])
    if questions:
        save_generated_questions(
            user_id=current_user.id,
            article_id=req.article_id,
            questions=questions,
            db=db
        )

    logger.info(f"用户 {current_user.id} 成功生成 {len(questions)} 道面试题")
    return {
        "success": True,
        "data": {"questions": questions},
        "error": None
    }


@router.post(
    "/simulate/start",
    summary="开始模拟面试",
    description="创建模拟面试会话，返回第一个问题"
)
async def start_simulate(
    req: StartSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    try:
        session = create_interview_session(
            resume_id=req.resume_id,
            jd_id=req.jd_id,
            db=db,
            user_id=current_user.id,
            user=current_user
        )
        logger.info(f"用户 {current_user.id} 开始模拟面试: session={session.id}")
        return {
            "success": True,
            "data": {
                "session_id": session.id,
                "question": session.current_question,
                "question_number": 1
            },
            "error": None
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/simulate/{session_id}/answer",
    summary="提交回答",
    description="提交当前问题回答，返回反馈和下一题"
)
async def submit_answer_endpoint(
    session_id: str,
    req: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    session = get_interview_session(session_id, db, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if session.status == "finished":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="面试已结束")

    try:
        feedback, next_question, is_finished = submit_interview_answer(
            session_id=session_id,
            answer=req.answer,
            db=db,
            user_id=current_user.id,
            user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    session = get_interview_session(session_id, db, current_user.id)
    question_count = len(session.questions or []) if session else 0

    return {
        "success": True,
        "data": {
            "feedback": feedback,
            "next_question": next_question,
            "is_finished": is_finished,
            "question_number": question_count
        },
        "error": None
    }


@router.get(
    "/simulate/{session_id}/summary",
    summary="获取面试总结",
    description="获取模拟面试完整总结，包含所有问答和反馈"
)
async def get_summary_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    summary = get_interview_summary(session_id, db, user_id=current_user.id, user=current_user)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return {"success": True, "data": summary, "error": None}