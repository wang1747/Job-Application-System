import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import func

from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # 昵称：仅用于界面展示，不作为登录标识
    name = Column(String, nullable=False)
    # 账号唯一标识：邮箱。注册时即绑定，登录仅支持邮箱 + 密码
    email = Column(String, nullable=True, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    role = Column(String, nullable=False, default="user", server_default="user")
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    
    # LLM 配置（BYOK）- 严格按照计划字段
    llm_provider = Column(String, nullable=True)
    llm_base_url = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
    encrypted_api_key = Column(Text, nullable=True)

    # 是否同意把简历/JD/面经贡献到共享语料库（默认关闭，需显式开启）
    allow_corpus = Column(Boolean, nullable=False, default=False, server_default="0")

    created_at = Column(DateTime, server_default=func.now())
