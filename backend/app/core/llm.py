from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import get_settings


@lru_cache
def get_llm() -> ChatOpenAI:
    """获取 LLM 实例（懒加载+缓存）"""
    settings = get_settings()
    return ChatOpenAI(
        api_key=settings.deepseek_api_key.get_secret_value(),
        base_url=settings.deepseek_base_url,
        model=settings.llm_model,
        temperature=0.1,
    )