from fastapi import APIRouter

from app.api.endpoints import (
    auth,
    users,
    douyin,
    social_accounts,
    content_collection,
    scheduled_tasks,
    notifications,
    comfyui,
    admin,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(douyin.router, prefix="/douyin", tags=["抖音管理"])
api_router.include_router(social_accounts.router, prefix="/social", tags=["社交账号"])
api_router.include_router(
    content_collection.router, prefix="/collection", tags=["内容采集"]
)
api_router.include_router(
    scheduled_tasks.router, prefix="/scheduled-tasks", tags=["定时任务"]
)
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知"])
api_router.include_router(comfyui.router, prefix="/comfyui", tags=["ComfyUI集成"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])
