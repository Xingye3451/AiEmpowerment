from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.api.v1 import auth, users, douyin, admin
from app.core.task_queue import TaskQueue

app = FastAPI(title="AiEmpowerment API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React 开发服务器
        "http://localhost:80",      # Nginx 生产环境
        "http://localhost",         # 不带端口的访问
        "http://frontend",          # Docker 容器间通信
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

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