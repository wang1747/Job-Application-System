from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.match_service import calculate_match, get_rankings

router = APIRouter()


class MatchRequest(BaseModel):
    jd_id: str
    resume_id: str


@router.post("/")
async def match(
    req: MatchRequest,
    db: Session = Depends(get_db)
):
    """计算 JD 与简历的匹配度（占位）"""
    result = calculate_match(req.jd_id, req.resume_id, db)
    return {"success": True, "data": result, "error": None}


@router.get("/rankings")
async def rankings(
    db: Session = Depends(get_db)
):
    """获取按匹配度排序的 JD 列表（占位）"""
    data = get_rankings(db)
    return {"success": True, "data": data, "error": None}