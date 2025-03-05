from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List
from pydantic import BaseModel
import os
from dotenv import load_dotenv, set_key
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_current_active_superuser, get_current_admin, get_db
from app.models.user import User
from app.core.config import settings, get_settings
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

router = APIRouter()


class SystemSettings(BaseModel):
    uploadDir: str
    maxUploadSize: int
    databaseUrl: str
    comfyuiUrl: str
    # 其他设置...


@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(
    current_user: User = Depends(get_current_active_superuser),
):
    """
    获取系统设置
    """
    # 只有超级管理员可以访问
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="没有权限访问此资源")

    # 从配置中获取设置
    config = get_settings()

    return {
        "uploadDir": config.UPLOAD_DIR,
        "maxUploadSize": config.MAX_UPLOAD_SIZE // (1024 * 1024),  # 转换为MB
        "databaseUrl": config.DATABASE_URL,
        "comfyuiUrl": config.COMFYUI_URL,
        # 其他设置...
    }


@router.post("/settings", response_model=Dict[str, Any])
async def update_system_settings(
    settings_data: SystemSettings,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    更新系统设置
    """
    # 只有超级管理员可以访问
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="没有权限访问此资源")

    # 获取.env文件路径
    env_path = os.path.join(os.getcwd(), ".env")

    # 如果.env文件不存在，创建一个空文件
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            pass

    # 加载当前环境变量
    load_dotenv(env_path)

    # 更新环境变量
    set_key(env_path, "UPLOAD_DIR", settings_data.uploadDir)
    set_key(
        env_path, "MAX_UPLOAD_SIZE", str(settings_data.maxUploadSize * 1024 * 1024)
    )  # 转换为字节
    set_key(env_path, "DATABASE_URL", settings_data.databaseUrl)
    set_key(env_path, "COMFYUI_URL", settings_data.comfyuiUrl)
    # 更新其他设置...

    # 重新加载环境变量
    load_dotenv(env_path, override=True)

    return {"message": "系统设置已更新，部分设置可能需要重启服务器才能生效"}


@router.get("/check-role", response_model=Dict[str, str])
async def check_admin_role(current_user: User = Depends(get_current_admin)):
    """
    检查当前用户是否为管理员
    """
    return {"role": current_user.role}


@router.get("/users", response_model=List[Dict[str, Any]])
async def get_all_users(
    db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)
):
    """获取所有用户列表（仅管理员）"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    # 将ORM对象转换为字典
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "role": user.role,
            "last_login": user.last_login,
        }
        for user in users
    ]


@router.post("/users", response_model=Dict[str, str])
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """创建新用户（仅管理员）"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="邮箱已存在")

    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        role="user",  # 默认为普通用户
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"message": "用户创建成功"}


@router.delete("/users/{user_id}", response_model=Dict[str, str])
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """删除用户（仅管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许删除管理员用户
    if user.role == "admin" and user_id != current_admin.id:
        raise HTTPException(status_code=400, detail="不能删除其他管理员用户")

    await db.delete(user)
    await db.commit()
    return {"message": "用户删除成功"}


@router.put("/users/{user_id}/reset-password", response_model=Dict[str, str])
async def reset_user_password(
    user_id: str,
    reset_data: dict,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """重置用户密码（仅管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许修改其他管理员密码
    if user.role == "admin" and user_id != current_admin.id:
        raise HTTPException(status_code=400, detail="不能修改其他管理员密码")

    # 更新密码
    user.hashed_password = get_password_hash(reset_data.get("new_password"))
    await db.commit()
    return {"message": "密码重置成功"}


@router.put("/users/{user_id}/toggle-status", response_model=Dict[str, str])
async def toggle_user_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """切换用户状态（启用/禁用）（仅管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许禁用管理员用户
    if user.role == "admin" and user_id != current_admin.id:
        raise HTTPException(status_code=400, detail="不能修改其他管理员状态")

    # 切换状态
    user.is_active = not user.is_active
    await db.commit()
    status = "启用" if user.is_active else "禁用"
    return {"message": f"用户已{status}"}


@router.put("/users/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """修改用户信息（仅管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许修改管理员用户
    if user.role == "admin" and user_id != current_admin.id:
        raise HTTPException(status_code=400, detail="不能修改其他管理员信息")

    # 检查邮箱是否被其他用户使用
    if user_data.email and user_data.email != user.email:
        result = await db.execute(
            select(User).where(User.email == user_data.email, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该邮箱已被使用")

    # 检查用户名是否被其他用户使用
    if user_data.username and user_data.username != user.username:
        result = await db.execute(
            select(User).where(User.username == user_data.username, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该用户名已被使用")

    # 更新用户信息
    if user_data.email:
        user.email = user_data.email
    if user_data.username:
        user.username = user_data.username

    await db.commit()
    await db.refresh(user)
    # 返回更新后的用户信息
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "role": user.role,
        "last_login": user.last_login,
    }


@router.put("/change-password", response_model=Dict[str, str])
async def change_admin_password(
    password_data: dict,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """管理员修改自己的密码"""
    # 验证当前密码
    if not verify_password(
        password_data.get("current_password"), current_admin.hashed_password
    ):
        raise HTTPException(status_code=400, detail="当前密码不正确")

    # 更新密码
    current_admin.hashed_password = get_password_hash(password_data.get("new_password"))
    await db.commit()
    return {"message": "密码修改成功"}
