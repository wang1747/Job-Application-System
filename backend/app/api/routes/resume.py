from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.config import get_settings

router = APIRouter()


@router.get("/list")
async def list_resumes(
    db: Session = Depends(get_db)
):
    """获取简历列表（占位）"""
    settings = get_settings()
    # 后续替换为 Resume 查询过滤 user_id
    return {"success": True, "data": [], "error": None}