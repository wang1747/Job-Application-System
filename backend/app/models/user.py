import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import func

from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)
    role = Column(String, nullable=False, default="user", server_default="user")
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    
    # LLM 配置（BYOK）- 严格按照计划字段
    llm_provider = Column(String, nullable=True)
    llm_base_url = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
    encrypted_api_key = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
