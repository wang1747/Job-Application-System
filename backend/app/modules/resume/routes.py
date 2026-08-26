from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.modules.auth.routes import get_current_user_required
from app.modules.resume.export_service import export_to_pdf, export_to_word
from app.modules.resume.parser import parse_resume_bytes
from app.modules.resume.services import (
    get_resume_versions,
    list_resumes,
    optimize_resume_flow,
    upload_resume,
)

router = APIRouter()


class ResumeUploadRequest(BaseModel):
    raw_text: str
    source_file: Optional[str] = None


class ResumeOptimizeRequest(BaseModel):
    resume_id: str
    jd_text: str = ""
    jd_id: Optional[str] = None


@router.get("/list")
async def get_resume_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    resumes = list_resumes(db, user_id=current_user.id)
    return {"success": True, "data": resumes, "error": None}


@router.post("/upload")
async def upload_resume_endpoint(
    req: ResumeUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    try:
        resume = upload_resume(
            raw_text=req.raw_text,
            source_file=req.source_file,
            db=db,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "success": True,
        "data": {"id": resume.id, "version": resume.version},
        "error": None,
    }


@router.post("/upload-file")
async def upload_resume_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件大小不能超过 10MB")

    try:
        raw_text = parse_resume_bytes(file.filename, content)
        resume = upload_resume(
            raw_text=raw_text,
            source_file=file.filename,
            db=db,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "success": True,
        "data": {
            "id": resume.id,
            "version": resume.version,
            "filename": file.filename,
        },
        "error": None,
    }


@router.get("/{resume_id}/versions")
async def get_resume_versions_endpoint(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
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


@router.post("/optimize")
async def optimize_resume_endpoint(
    req: ResumeOptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    try:
        result = await optimize_resume_flow(
            req.resume_id,
            req.jd_text,
            db,
            current_user,
            jd_id=req.jd_id,
        )
    except ValueError as exc:
        if str(exc) == "resume_not_found":
            raise HTTPException(status_code=404, detail="简历不存在")
        if str(exc) == "jd_not_found":
            raise HTTPException(status_code=404, detail="目标 JD 不存在")
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.get("/{resume_id}/export")
async def export_resume(
    resume_id: str,
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    from app.models.resume import Resume

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    fmt = format.lower()
    if fmt == "pdf":
        content = export_to_pdf(resume)
        media_type = "application/pdf"
        filename = f"resume_{resume_id}.pdf"
    elif fmt in ("word", "docx"):
        content = export_to_word(resume)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"resume_{resume_id}.docx"
    else:
        raise HTTPException(status_code=400, detail="不支持的格式，请使用 pdf 或 word")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
