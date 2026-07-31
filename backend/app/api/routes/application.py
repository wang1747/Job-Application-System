from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date
from app.services.reminder_service import get_reminders, get_company_interview_articles

from app.core.database import get_db
from app.services.application_service import (
    create_application, list_applications, get_application,
    update_application_status, delete_application, get_statistics
)

router = APIRouter()


class CreateApplicationRequest(BaseModel):
    company: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    jd_id: Optional[str] = None
    resume_id: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: Literal["saved", "applied", "online_test", "first_interview", "second_interview", "hr_round", "offered", "accepted", "rejected"] = Field(...)


class ApplicationOut(BaseModel):
    id: str
    company: str
    position: str
    status: str
    jd_id: Optional[str]
    resume_id: Optional[str]
    applied_date: Optional[date]
    next_action: Optional[str]
    next_action_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/")
async def create_application_endpoint(
    req: CreateApplicationRequest,
    db: Session = Depends(get_db)
):
    """创建投递记录"""
    try:
        app = create_application(
            company=req.company,
            position=req.position,
            jd_id=req.jd_id,
            resume_id=req.resume_id,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "data": {"id": app.id}, "error": None}


@router.get("/")
async def list_applications_endpoint(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="按状态筛选")
):
    """获取投递列表"""
    apps = list_applications(db, status)
    return {"success": True, "data": [ApplicationOut.model_validate(item) for item in apps], "error": None}


@router.get("/stats")
async def get_statistics_endpoint(
    db: Session = Depends(get_db)
):
    """获取投递统计数据"""
    stats = get_statistics(db)
    return {"success": True, "data": stats, "error": None}


@router.get("/{app_id}")
async def get_application_endpoint(
    app_id: str,
    db: Session = Depends(get_db)
):
    """获取单个投递记录"""
    app = get_application(app_id, db)
    if not app:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return {"success": True, "data": ApplicationOut.model_validate(app), "error": None}


@router.put("/{app_id}/status")
async def update_status_endpoint(
    app_id: str,
    req: UpdateStatusRequest,
    db: Session = Depends(get_db)
):
    """更新投递状态"""
    try:
        app = update_application_status(app_id, req.status, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not app:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return {"success": True, "data": {"id": app.id, "status": app.status}, "error": None}


@router.delete("/{app_id}")
async def delete_application_endpoint(
    app_id: str,
    db: Session = Depends(get_db)
):
    """删除投递记录"""
    if not delete_application(app_id, db):
        raise HTTPException(status_code=404, detail="投递记录不存在")
    return {"success": True, "data": None, "error": None}

@router.get("/reminders")
async def get_reminders_endpoint(
    db: Session = Depends(get_db)
):
    """获取提醒汇总（超期跟进 + 即将到来的面试）"""
    reminders = get_reminders(db)
    return {"success": True, "data": reminders, "error": None}


@router.get("/{app_id}/interview-articles")
async def get_interview_articles_for_application(
    app_id: str,
    db: Session = Depends(get_db)
):
    """获取某投递对应的公司面经（面试前推送）"""
    from app.services.application_service import get_application
    app = get_application(app_id, db)
    if not app:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    
    articles = get_company_interview_articles(app.company, db)
    return {"success": True, "data": articles, "error": None}