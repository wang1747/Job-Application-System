import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)
    
    # LLM 配置（BYOK）- 严格按照计划字段
    llm_provider = Column(String, nullable=True)
    llm_base_url = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
    encrypted_api_key = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())