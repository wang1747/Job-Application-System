from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.config import get_settings
from app.models.jd import JobDescription
from app.agents.graphs.jd_analysis import analyze_jd

router = APIRouter()


# 请求体
class JDParseRequest(BaseModel):
    raw_text: str


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
async def parse_jd(
    req: JDParseRequest,
    db: Session = Depends(get_db)
):
    """解析 JD 文本，AI 结构化提取信息"""
    settings = get_settings()
    
    # 执行 LangGraph 工作流
    result = await analyze_jd(req.raw_text)
    
    if result.get("error"):
        return {"success": False, "data": None, "error": result["error"]}
    
    parsed = result.get("parsed", {})
    try:
        # 存入数据库
        jd = JobDescription(
            user_id=settings.default_user_id,
            raw_text=req.raw_text,
            company=parsed.get("company"),
            position=parsed.get("position"),
            must_have=parsed.get("must_have"),
            nice_to_have=parsed.get("nice_to_have"),
            tech_stack=parsed.get("tech_stack"),
            hidden_signals=parsed.get("hidden_signals"),
        )
        db.add(jd)
        db.commit()
        db.refresh(jd)
    except Exception as e:
        db.rollback()
        return {"success": False, "data": None, "error": f"数据库保存失败: {str(e)}"}
    
    return {"success": True, "data": {"id": jd.id, "parsed": parsed}, "error": None}


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
    return {"success": True, "data": None, "error": None}