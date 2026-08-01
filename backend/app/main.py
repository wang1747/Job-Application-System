from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.database import init_db, SessionLocal
from .config import get_settings
from .models.user import User
# 导入所有业务路由
from .api.routes import jd, resume, match, interview, application


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    init_db()
    
    # 创建默认用户
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
            print(f"⚠️ 种子数据生成失败: {e}")
            
    finally:
        db.close()
    
    yield


app = FastAPI(
    title="OfferFlow API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 开发配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有业务接口路由
app.include_router(jd.router, prefix="/api/v1/jd", tags=["JD解析模块"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["简历模块"])
app.include_router(match.router, prefix="/api/v1/match", tags=["匹配分析模块"])
app.include_router(interview.router, prefix="/api/v1/interview", tags=["面试备考模块"])
app.include_router(application.router, prefix="/api/v1/applications", tags=["投递追踪模块"])


@app.get("/api/health")
async def health_check():
    return {"success": True, "data": {"status": "ok", "message": "OfferFlow is running"}, "error": None}
