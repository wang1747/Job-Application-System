from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.match_service import calculate_match, get_match_detail, get_rankings

router = APIRouter()


class MatchRequest(BaseModel):
    jd_id: str
    resume_id: str


@router.post("")
@router.post("/")
async def match(
    req: MatchRequest,
    db: Session = Depends(get_db)
):
    """计算 JD 与简历的匹配度并保存结果"""
    try:
        result = calculate_match(req.jd_id, req.resume_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True, "data": result, "error": None}


@router.get("/rankings")
async def rankings(
    db: Session = Depends(get_db)
):
    """获取按匹配度排序的 JD 列表"""
    data = get_rankings(db)
    return {"success": True, "data": data, "error": None}


@router.get("/{match_id}")
async def match_detail(
    match_id: str,
    db: Session = Depends(get_db)
):
    """获取匹配结果详情"""
    result = get_match_detail(match_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="匹配结果不存在")
    return {"success": True, "data": result, "error": None}
