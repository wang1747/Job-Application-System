from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...config import get_settings

router = APIRouter()


@router.get("/")
async def list_applications(
    db: Session = Depends(get_db)
):
    """获取投递列表（占位）"""
    settings = get_settings()
    return {"success": True, "data": [], "error": None}
