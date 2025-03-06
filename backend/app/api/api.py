from fastapi import APIRouter

# 导入v1目录下的路由
from app.api.v1 import (
    auth as auth_v1,
    users as users_v1,
    douyin as douyin_v1,
    social_accounts as social_accounts_v1,
    content_collection as content_collection_v1,
    scheduled_tasks as scheduled_tasks_v1,
    admin as admin_v1,
    notifications as notifications_v1,
)

api_router = APIRouter()

# 注册v1目录下的路由
api_router.include_router(auth_v1.router, prefix="/auth", tags=["认证"])
api_router.include_router(users_v1.router, prefix="/users", tags=["用户"])
api_router.include_router(douyin_v1.router, prefix="/douyin", tags=["抖音管理"])
api_router.include_router(
    social_accounts_v1.router, prefix="/social", tags=["社交账号"]
)
api_router.include_router(
    content_collection_v1.router, prefix="/collection", tags=["内容采集"]
)
api_router.include_router(
    scheduled_tasks_v1.router, prefix="/scheduled-tasks", tags=["定时任务"]
)
api_router.include_router(admin_v1.router, prefix="/admin", tags=["管理员"])
api_router.include_router(
    notifications_v1.router, prefix="/notifications", tags=["通知"]
)
