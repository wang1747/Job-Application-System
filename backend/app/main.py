from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .core.database import init_db, SessionLocal
from .models.user import User
from .api.routes import application, auth, interview, jd, match, resume


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    settings = get_settings()
    db = SessionLocal()
    try:
        default_user = db.query(User).filter(User.id == settings.default_user_id).first()
        if not default_user:
            default_user = User(id=settings.default_user_id, name="默认用户")
            db.add(default_user)
            db.commit()
            print("[OK] 默认用户已创建")

        try:
            from app.seed import seed_demo_data
            seed_demo_data(db)
        except Exception as e:
            print(f"[ERROR] 种子数据生成失败: {e}")
    finally:
        db.close()

    yield


app = FastAPI(
    title="OfferFlow API",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jd.router, prefix="/api/v1/jd", tags=["JD解析模块"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["简历模块"])
app.include_router(match.router)
app.include_router(interview.router)
app.include_router(application.router)
app.include_router(auth.router)


@app.get("/api/health")
async def health_check():
    return {"success": True, "data": {"status": "ok", "message": "OfferFlow is running"}, "error": None}
