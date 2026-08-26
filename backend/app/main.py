import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.exceptions import register_exception_handlers
from app.core.security import hash_password
from app.modules.application.reminder_push_service import push_reminders_for_user
from app.modules.application import router as application_router
from app.modules.admin import router as admin_router
from app.modules.auth import router as auth_router
from app.modules.interview import router as interview_router
from app.modules.jd import router as jd_router
from app.modules.match import router as match_router
from app.modules.model_config import router as model_config_router
from app.modules.observability import router as observability_router
from app.modules.resume import router as resume_router

from .config import get_settings
from .core.database import init_db, SessionLocal
from .models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    settings = get_settings()
    db = SessionLocal()
    try:
        default_user = db.query(User).filter(User.id == settings.default_user_id).first()
        if not default_user:
            default_user = User(id=settings.default_user_id, name=settings.default_user_name)
            db.add(default_user)
            db.commit()
            print("[OK] 默认用户已创建")
        elif default_user.name != settings.default_user_name:
            default_user.name = settings.default_user_name
            db.commit()

        if not default_user.hashed_password:
            default_user.hashed_password = hash_password(settings.default_user_password)
            db.commit()
            print("[OK] 默认用户密码已初始化")

        try:
            from app.seed import seed_demo_data
            seed_demo_data(db)
        except Exception as e:
            print(f"[ERROR] 种子数据生成失败: {e}")
    finally:
        db.close()

    reminder_task = None
    if settings.reminder_webhook_url:
        async def reminder_loop():
            while True:
                await asyncio.sleep(settings.reminder_check_interval_minutes * 60)
                reminder_db = SessionLocal()
                try:
                    users = reminder_db.query(User).all()
                    for user in users:
                        try:
                            await push_reminders_for_user(
                                webhook_url=settings.reminder_webhook_url,
                                db=reminder_db,
                                user=user,
                            )
                        except Exception as e:
                            logging.getLogger(__name__).error("提醒推送失败: %s", e)
                finally:
                    reminder_db.close()

        reminder_task = asyncio.create_task(reminder_loop())

    yield

    if reminder_task:
        reminder_task.cancel()


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

app.include_router(jd_router, prefix="/api/v1/jd", tags=["JD解析模块"])
app.include_router(resume_router, prefix="/api/v1/resume", tags=["简历模块"])
app.include_router(match_router)
app.include_router(interview_router)
app.include_router(application_router)
app.include_router(auth_router)
app.include_router(model_config_router)
app.include_router(admin_router)
app.include_router(observability_router)

register_exception_handlers(app)

@app.get("/api/health")
async def health_check():
    return {"success": True, "data": {"status": "ok", "message": "OfferFlow is running"}, "error": None}
