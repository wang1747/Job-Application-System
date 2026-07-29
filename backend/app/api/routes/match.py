from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.config import get_settings

router = APIRouter()


@router.get("/rankings")
async def get_rankings(
    db: Session = Depends(get_db)
):
    """获取批量 JD 排名（占位）"""
    settings = get_settings()
    return {"success": True, "data": [], "error": None}