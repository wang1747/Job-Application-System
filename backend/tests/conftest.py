import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base


@pytest.fixture
def db_session():
    """内存 SQLite 数据库测试夹具"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_jd_text() -> str:
    return "ByteDance hiring Python backend engineer, bachelor's degree required, 3+ years Python experience."


@pytest.fixture
def sample_resume_text() -> str:
    return "John Doe, CS Master, 5 years Python experience, familiar with Django and FastAPI."
