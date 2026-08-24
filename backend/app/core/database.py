from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from ..config import get_settings

settings = get_settings()

# 创建数据库引擎
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ORM 基类（SQLAlchemy 2.0 标准）
class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        for column in (
            "hashed_password",
            "llm_provider",
            "llm_base_url",
            "llm_model",
            "encrypted_api_key",
            "role",
            "is_active",
        ):
            if column in columns:
                continue
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {column} VARCHAR"))
        with engine.begin() as conn:
            conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
        with engine.begin() as conn:
            conn.execute(text("UPDATE users SET is_active = 1 WHERE is_active IS NULL"))
