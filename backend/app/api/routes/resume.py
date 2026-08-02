from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.services.resume_service import list_resumes, upload_resume, get_resume_versions, save_optimized_version
from app.agents.tools.resume_parser import parse_resume_bytes
from app.agents.graphs.resume_optimize import optimize_resume
from app.agents.tools.ats_checker import check_ats_compatibility
from app.models.resume import Resume
from app.api.routes.auth import get_current_user_required
from app.models.user import User

router = APIRouter()


class ResumeUploadRequest(BaseModel):
    raw_text: str
    source_file: Optional[str] = None


@router.get("/list")
async def get_resume_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """获取简历列表"""
    resumes = list_resumes(db, user_id=current_user.id)
    return {"success": True, "data": resumes, "error": None}


@router.post("/upload")
async def upload_resume_endpoint(
    req: ResumeUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """上传简历文本"""
    resume = upload_resume(
        raw_text=req.raw_text,
        source_file=req.source_file,
        db=db,
        user_id=current_user.id
    )
    return {"success": True, "data": {"id": resume.id, "version": resume.version}, "error": None}


@router.post("/upload-file")
async def upload_resume_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
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
        db=db,
        user_id=current_user.id
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


@router.get("/{resume_id}/versions")
async def get_resume_versions_endpoint(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """获取简历版本历史"""
    versions = get_resume_versions(resume_id, db, user_id=current_user.id)
    if versions is None:
        raise HTTPException(status_code=404, detail="简历不存在")
    return {
        "success": True,
        "data": [
            {
                "id": v.id,
                "version": v.version,
                "raw_text": v.raw_text,
                "source_file": v.source_file,
                "parsed_json": v.parsed_json,
                "created_at": v.created_at,
            }
            for v in versions
        ],
        "error": None,
    }


class ResumeOptimizeRequest(BaseModel):
    resume_id: str
    jd_text: str


@router.post("/optimize")
async def optimize_resume_endpoint(
    req: ResumeOptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """针对 JD 优化简历"""
    # 获取简历
    resume = db.query(Resume).filter(
        Resume.id == req.resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    
    # 执行优化
    result = await optimize_resume(resume.raw_text, req.jd_text)
    
    if result.get("error"):
        return {"success": False, "data": None, "error": result["error"]}

    optimized = result.get("optimized", "")
    changes = result.get("changes", [])
    new_version = None
    if optimized and optimized.strip():
        new_version = save_optimized_version(
            req.resume_id,
            optimized,
            changes,
            db,
            user_id=current_user.id
        )
    
    return {
        "success": True,
        "data": {
            "optimized": optimized,
            "changes": changes,
            "ats": check_ats_compatibility(resume.raw_text, req.jd_text),
            "ats_after": check_ats_compatibility(optimized, req.jd_text),
            "new_version": {
                "id": new_version.id,
                "version": new_version.version,
            } if new_version else None,
        },
        "error": None
    }