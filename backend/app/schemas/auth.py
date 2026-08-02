"""
认证模块 Pydantic 模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    email: Optional[str] = None
    role: Optional[str] = None

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="用户名，1-32字符",
        examples=["zhangsan"]
    )
    password: str = Field(
        ...,
        min_length=6,
        description="密码最少6位，建议同时包含大小写字母、数字",
        examples=["Pass123456"]
    )


class RegisterResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名", examples=["zhangsan"])
    password: str = Field(..., description="密码", examples=["Pass123456"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

    model_config = {"from_attributes": True}


__all__ = [
    "UserResponse",
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
]