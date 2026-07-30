from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.resume_service import list_resumes, upload_resume

router = APIRouter()


# 请求体
class ResumeUploadRequest(BaseModel):
    raw_text: str
    source_file: str | None = None


@router.get("/list")
async def get_resume_list(
    db: Session = Depends(get_db)
):
    """获取简历列表"""
    resumes = list_resumes(db)
    return {"success": True, "data": resumes, "error": None}


@router.post("/upload")
async def upload_resume_endpoint(
    req: ResumeUploadRequest,
    db: Session = Depends(get_db)
):
    """上传简历文本"""
    resume = upload_resume(
        raw_text=req.raw_text,
        source_file=req.source_file,
        db=db
    )
    return {"success": True, "data": {"id": resume.id, "version": resume.version}, "error": None}