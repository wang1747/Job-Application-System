from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.services.resume_service import list_resumes, upload_resume
from app.agents.tools.resume_parser import parse_resume_bytes

router = APIRouter()


class ResumeUploadRequest(BaseModel):
    raw_text: str
    source_file: Optional[str] = None


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


@router.post("/upload-file")
async def upload_resume_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传简历文件（PDF/MD/TXT）"""
    content = await file.read()
    
    try:
        raw_text = parse_resume_bytes(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    resume = upload_resume(
        raw_text=raw_text,
        source_file=file.filename,
        db=db
    )
    
    return {
        "success": True,
        "data": {
            "id": resume.id,
            "version": resume.version,
            "filename": file.filename
        },
        "error": None
    }