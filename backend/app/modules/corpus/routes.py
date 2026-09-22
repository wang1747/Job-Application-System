from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.routes import get_current_user_required
from app.models.user import User
from app.modules.corpus.services import (
    add_corpus_item,
    retrieve_similar,
    list_corpus,
    delete_corpus,
    count_corpus,
    set_corpus_consent,
    get_corpus_consent,
)
from app.modules.corpus.schemas import CorpusAddRequest, CorpusSearchRequest

router = APIRouter()


class ConsentRequest(BaseModel):
    allow: bool


@router.get("/consent")
async def get_consent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """查询当前用户是否同意贡献语料。"""
    return {"success": True, "data": {"allow_corpus": get_corpus_consent(db, current_user.id)}, "error": None}


@router.post("/consent")
async def set_consent(
    req: ConsentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """开启/关闭「贡献语料到共享语料库」（默认关闭）。"""
    set_corpus_consent(db, current_user.id, req.allow)
    return {"success": True, "data": {"allow_corpus": req.allow}, "error": None}


@router.post("/add")
async def add_corpus(
    req: CorpusAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    """贡献一条语料（简历/JD/面经）到共享语料库。"""
    if not req.raw_text or len(req.raw_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="语料内容过短（至少 20 字）")
    if req.item_type not in ("resume", "jd", "interview"):
        raise HTTPException(status_code=400, detail="item_type 只能是 resume/jd/interview")
    item = add_corpus_item(
        item_type=req.item_type,
        raw_text=req.raw_text,
        db=db,
        structured=req.structured,
        tags=req.tags,
        source="user_upload",
        user_id=current_user.id,
        is_public=req.is_public,
    )
    return {
        "success": True,
        "data": {
            "id": item.id,
            "item_type": item.item_type,
            "direction": item.direction,
            "tags": item.tags,
        },
        "error": None,
    }


@router.post("/search")
async def search_corpus(
    req: CorpusSearchRequest,
    db: Session = Depends(get_db),
):
    """检索语料库中最相似的 N 条（RAG 检索入口，只读公开，供桌面版/网页版共用）。"""
    results = retrieve_similar(
        query_text=req.query_text,
        top_k=req.top_k,
        item_type=req.item_type,
        direction=req.direction,
        db=db,
    )
    return {"success": True, "data": results, "error": None}


@router.get("/list")
async def list_corpus_route(
    item_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    items = list_corpus(db, item_type=item_type)
    data = [
        {
            "id": i.id,
            "item_type": i.item_type,
            "direction": i.direction,
            "tags": i.tags,
            "source": i.source,
            "is_public": i.is_public,
            "raw_text_preview": (i.raw_text or "")[:200],
            "created_at": str(i.created_at) if i.created_at else None,
        }
        for i in items
    ]
    return {"success": True, "data": data, "error": None}


@router.get("/stats")
async def corpus_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    return {"success": True, "data": count_corpus(db), "error": None}


@router.delete("/{item_id}")
async def delete_corpus_route(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    if not delete_corpus(item_id, db):
        raise HTTPException(status_code=404, detail="语料不存在")
    return {"success": True, "data": None, "error": None}
