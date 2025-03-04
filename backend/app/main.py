from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import os
from app.api.v1 import auth, users, douyin, admin
from app.core.task_queue import TaskQueue
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建必要的目录
os.makedirs("static/videos", exist_ok=True)
os.makedirs("static/previews", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/processed_videos", exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 获取任务队列实例
task_queue = TaskQueue()


@app.on_event("startup")
async def startup_event():
    # 启动任务队列处理器
    asyncio.create_task(task_queue.process_tasks())


# 包含路由
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(douyin.router, prefix="/api/v1/douyin", tags=["douyin"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/")
async def root():
    return {"message": "Welcome to AiEmpowerment API"}
