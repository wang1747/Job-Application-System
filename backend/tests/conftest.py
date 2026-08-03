import json
import os
import sys

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User


class FakeLLM:
    """离线测试用的 LLM，按 prompt 关键字返回对应 JSON"""

    def invoke(self, messages):
        content = "\n".join(getattr(m, "content", "") or "" for m in messages)
        if "JD parser" in content:
            payload = {
                "company": "ByteDance",
                "position": "Backend Engineer",
                "must_have": ["Python", "本科"],
                "nice_to_have": ["Docker"],
                "tech_stack": {
                    "backend": ["Python", "FastAPI"],
                    "frontend": [],
                    "infra": ["Docker"],
                    "other": [],
                },
                "hidden_signals": ["团队扩张快"],
            }
        elif "简历优化专家" in content:
            payload = {
                "optimized": "优化后的简历内容，突出 Python 和高并发经验。",
                "changes": ["突出了 Python 经验", "补充了量化成果"],
            }
        elif "面试题生成专家" in content:
            payload = {
                "questions": [
                    {"question": "讲一下你最有挑战的项目", "category": "项目", "difficulty": "中等"}
                ]
            }
        elif "资深面试官" in content:
            return AIMessage(content="整体表现不错，注意结构化表达。")
        elif "专业的面试官" in content:
            return AIMessage(content="请介绍一下你的项目经验。")
        else:
            payload = {"questions": [], "tags": [], "difficulty": None}
        return AIMessage(content=json.dumps(payload, ensure_ascii=False))


@pytest.fixture(autouse=True)
def _fake_llm(monkeypatch):
    """所有测试使用离线 LLM，避免外网依赖"""
    fake = FakeLLM()

    import app.agents.graphs.interview_prep as interview_prep
    import app.agents.graphs.jd_analysis as jd_analysis
    import app.agents.graphs.mock_interview as mock_interview
    import app.agents.graphs.resume_optimize as resume_optimize
    import app.services.interview_service as interview_service

    monkeypatch.setattr(jd_analysis, "get_user_llm_or_raise", lambda user: fake)
    monkeypatch.setattr(resume_optimize, "get_user_llm_or_raise", lambda user: fake)
    monkeypatch.setattr(interview_prep, "get_user_llm_or_raise", lambda user: fake)
    monkeypatch.setattr(mock_interview, "get_user_llm_or_raise", lambda user: fake)
    monkeypatch.setattr(interview_service, "get_user_llm_or_raise", lambda user: fake)
    return fake


@pytest.fixture
def db_session():
    """内存 SQLite 数据库测试夹具"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    session.add(User(id="default", name="默认用户"))
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_client(tmp_path):
    """FastAPI TestClient 实例：临时文件数据库 + 离线 LLM，线程安全"""
    from app.config import get_settings
    settings = get_settings()
    settings.chroma_persist_path = str(tmp_path / "chroma")

    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with TestingSession() as session:
        session.add(User(id="default", name="默认用户"))
        session.commit()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def client(auth_client):
    from app.api.routes.auth import get_current_user_required

    def override_current_user():
        return User(id="default", name="默认用户")

    app.dependency_overrides[get_current_user_required] = override_current_user
    yield auth_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_jd_text() -> str:
    return "ByteDance hiring Python backend engineer, bachelor's degree required, 3+ years Python experience."


@pytest.fixture
def sample_resume_text() -> str:
    return "John Doe, CS Master, 5 years Python experience, familiar with Django and FastAPI."
