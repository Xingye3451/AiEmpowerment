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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],  # 允许的前端域名，添加通配符以便测试
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 创建必要的目录
os.makedirs("static/videos", exist_ok=True)
os.makedirs("static/previews", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/processed_videos", exist_ok=True)

# 打印目录路径，便于调试
print(f"静态文件目录: {os.path.abspath('static')}")
print(f"上传文件目录: {os.path.abspath('uploads')}")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")


# 添加中间件，打印所有请求信息，便于调试
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"请求: {request.method} {request.url}")
    response = await call_next(request)
    print(f"响应: {response.status_code}")
    return response


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
