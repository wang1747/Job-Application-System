from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "offerflow.db"


class Settings(BaseSettings):
    # LLM 配置
    deepseek_api_key: str  # 必填，需在 .env 配置 DEEPSEEK_API_KEY
    deepseek_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    # 数据库
    database_url: str = f"sqlite:///{DB_PATH.as_posix()}"

    # 向量库 ChromaDB 持久化路径
    chroma_persist_path: str = "./chroma_db"

    # 默认用户
    default_user_id: str = "default"

    @model_validator(mode="after")
    def _resolve_project_paths(self):
        if self.database_url.startswith("sqlite:///./"):
            relative = self.database_url[len("sqlite:///./"):]
            self.database_url = f"sqlite:///{(PROJECT_ROOT / relative).as_posix()}"
        if not Path(self.chroma_persist_path).is_absolute():
            self.chroma_persist_path = str(PROJECT_ROOT / self.chroma_persist_path)
        return self

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
