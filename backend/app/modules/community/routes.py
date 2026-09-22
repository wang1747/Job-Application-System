"""社区分享路由：发帖、列表、详情、评论、点赞、删除。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.routes import get_current_user_required
from app.modules.permissions import ROLE_ADMIN, require_role
from app.models.user import User
from app.modules.community import services as svc

router = APIRouter(prefix="/api/v1/community", tags=["社区交流模块"])


class CreatePostRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    category: str = Field(default="经验分享")
    tags: Optional[List[str]] = None


class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


@router.post("/posts")
async def create_post(
    req: CreatePostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    post = svc.create_post(db, current_user.id, req.title, req.content, req.category, req.tags)
    return {"success": True, "data": {"id": post.id}, "error": None}


@router.get("/posts")
async def list_posts(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    result = svc.list_posts(db, category=category, page=page, page_size=page_size)
    return {"success": True, "data": result, "error": None}


@router.get("/posts/{post_id}")
async def get_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    detail = svc.get_post_detail(db, post_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")
    return {"success": True, "data": detail, "error": None}


@router.post("/posts/{post_id}/comments")
async def add_comment(
    post_id: str,
    req: CreateCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    try:
        comment = svc.add_comment(db, post_id, current_user.id, req.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"success": True, "data": {"id": comment.id}, "error": None}


@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    try:
        result = svc.toggle_like(db, post_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"success": True, "data": result, "error": None}


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    is_admin = current_user.role == ROLE_ADMIN
    try:
        ok = svc.delete_post(db, post_id, current_user.id, is_admin=is_admin)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")
    return {"success": True, "data": None, "error": None}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(ROLE_ADMIN)),
):
    ok = svc.delete_comment(db, comment_id, is_admin=True)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评论不存在")
    return {"success": True, "data": None, "error": None}
