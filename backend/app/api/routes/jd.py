from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.jd_service import parse_and_save, list_jds, delete_jd

router = APIRouter()


class JDParseRequest(BaseModel):
    raw_text: str


@router.get("/list")
async def list_jds_route(
    db: Session = Depends(get_db)
):
    jds = list_jds(db)
    return {"success": True, "data": jds, "error": None}


@router.post("/parse")
async def parse_jd(
    req: JDParseRequest,
    db: Session = Depends(get_db)
):
    result = await parse_and_save(raw_text=req.raw_text, db=db)
    return result


@router.delete("/{jd_id}")
async def delete_jd_route(
    jd_id: str,
    db: Session = Depends(get_db)
):
    if not delete_jd(jd_id, db):
        raise HTTPException(status_code=404, detail="JD does not exist")
    return {"success": True, "data": None, "error": None}
