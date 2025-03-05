from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import asyncio
from app.api.api import api_router
from app.core.config import settings
from app.core.scheduler import init_scheduler, shutdown_scheduler
from app.db.database import engine
from app.db.init_db import init_db, ensure_db_exists
from app.db.base_class import Base

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 确保数据库文件存在
ensure_db_exists()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # 明确允许前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["X-Process-Time"],
)


# 添加请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 添加API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("应用启动")
    # 初始化数据库
    await init_db()
    # 初始化调度器
    init_scheduler()


# 应用关闭事件
@app.on_event("shutdown")
def shutdown_event():
    logger.info("应用关闭")
    # 关闭调度器
    shutdown_scheduler()


@app.get("/")
def root():
    return {"message": "欢迎使用AI赋能内容分发平台API"}
