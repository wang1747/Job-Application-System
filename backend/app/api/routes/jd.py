from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...config import get_settings
from ...models.jd import JobDescription

router = APIRouter()


@router.get("/list")
async def list_jds(
    db: Session = Depends(get_db)
):
    """获取所有 JD 列表"""
    settings = get_settings()
    jds = db.query(JobDescription).filter(
        JobDescription.user_id == settings.default_user_id
    ).order_by(JobDescription.created_at.desc()).all()
    return {"success": True, "data": jds, "error": None}


@router.post("/parse")
async def parse_jd():
    """解析 JD（暂为占位，后续实现 LangGraph 工作流）"""
    return {"success": True, "data": None, "error": None, "message": "JD 解析功能开发中"}


@router.delete("/{jd_id}")
async def delete_jd(
    jd_id: str,
    db: Session = Depends(get_db)
):
    """删除 JD"""
    settings = get_settings()
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == settings.default_user_id
    ).first()
    
    if not jd:
        raise HTTPException(status_code=404, detail="JD 不存在")
    
    db.delete(jd)
    db.commit()
    return {"success": True, "data": None, "error": None, "message": "删除成功"}
