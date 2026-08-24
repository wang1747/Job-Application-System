from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import File, UploadFile
from pydantic import BaseModel

from app.core.database import get_db
from app.modules.jd.services import parse_and_save, list_jds, delete_jd
from app.modules.auth.routes import get_current_user_required
from app.models.user import User
from app.modules.jd.ocr_service import extract_text_from_image_file

router = APIRouter()


class JDParseRequest(BaseModel):
    raw_text: str


@router.get("/list")
async def list_jds_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    jds = list_jds(db, user_id=current_user.id)
    return {"success": True, "data": jds, "error": None}


@router.post("/parse")
async def parse_jd(
    req: JDParseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    result = await parse_and_save(raw_text=req.raw_text, db=db, user_id=current_user.id)
    return result

@router.post("/ocr")
async def ocr_import_jd(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """
    通过截图 OCR 导入 JD
    上传图片，自动识别文字内容并解析
    """
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件大小不能超过 10MB")
    
    try:
        raw_text = extract_text_from_image_file(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="OCR 识别结果为空，请确保图片清晰包含文字"
        )
    
    result = await parse_and_save(raw_text, db, user_id=current_user.id)
    
    if result.get("error"):
        return {"success": False, "data": None, "error": result["error"]}
    
    return {
        "success": True,
        "data": {
            "id": result["data"]["id"],
            "parsed": result["data"]["parsed"],
            "ocr_text": raw_text[:500] + ("..." if len(raw_text) > 500 else ""),
        },
        "error": None,
    }

@router.delete("/{jd_id}")
async def delete_jd_route(
    jd_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    if not delete_jd(jd_id, db, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="JD does not exist")
    return {"success": True, "data": None, "error": None}
