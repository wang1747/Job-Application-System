from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User
from app.modules.permissions import ROLE_ADMIN, ROLE_USER, require_role

router = APIRouter(prefix="/api/v1/admin", tags=["系统管理"])


class UserOut(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern=f"^({ROLE_ADMIN}|{ROLE_USER})$")


class ActiveUpdateRequest(BaseModel):
    is_active: bool


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6, description="新密码（至少 6 位）")


@router.get("/users", response_model=dict)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(ROLE_ADMIN)),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "success": True,
        "data": [UserOut.model_validate(user) for user in users],
        "error": None,
    }


@router.put("/users/{user_id}/role", response_model=dict)
def update_user_role(
    user_id: str,
    req: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ROLE_ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if user.id == current_user.id and req.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能取消自己的管理员角色")
    user.role = req.role
    db.commit()
    db.refresh(user)
    return {"success": True, "data": UserOut.model_validate(user), "error": None}


@router.put("/users/{user_id}/active", response_model=dict)
def update_user_active(
    user_id: str,
    req: ActiveUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(ROLE_ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if user.id == current_user.id and not req.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用当前管理员账号")
    user.is_active = req.is_active
    db.commit()
    db.refresh(user)
    return {"success": True, "data": UserOut.model_validate(user), "error": None}


@router.post("/users/{user_id}/reset_password", response_model=dict)
def reset_user_password(
    user_id: str,
    req: PasswordResetRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(ROLE_ADMIN)),
):
    """管理员重置任意用户密码（忘记密码时的恢复入口）。"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"success": True, "data": {"id": user.id, "name": user.name}, "error": None}
