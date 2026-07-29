from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...config import get_settings

router = APIRouter()


@router.get("/questions")
async def get_questions(
    db: Session = Depends(get_db)
):
    """获取面试题列表（占位）"""
    settings = get_settings()
    return {"success": True, "data": [], "error": None}
