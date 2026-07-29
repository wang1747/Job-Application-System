from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM 配置
    deepseek_api_key: str  # 必填，需在 .env 配置 DEEPSEEK_API_KEY
    deepseek_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    # 数据库
    database_url: str = "sqlite:///./offerflow.db"

    # 向量库 ChromaDB 持久化路径
    chroma_persist_path: str = "./chroma_db"

    # 默认用户
    default_user_id: str = "default"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()