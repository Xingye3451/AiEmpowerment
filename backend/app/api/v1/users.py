from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import secrets

from app.core.security import get_password_hash
from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    User as UserSchema,
    PasswordReset,
    PasswordResetVerify,
)

router = APIRouter()


@router.post("/", response_model=UserSchema)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalar_one_or_none()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email, username=user.username, hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.get("/me", response_model=UserSchema)
async def read_user_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "role": current_user.role,
        "last_login": current_user.last_login,
    }


@router.post("/reset-password-request")
async def request_password_reset(email: str, db: AsyncSession = Depends(get_db)):
    # 查找用户
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邮箱未注册")

    # 生成重置令牌
    reset_token = secrets.token_urlsafe(32)
    reset_token_expires = datetime.utcnow() + timedelta(hours=24)

    # 保存重置令牌到用户记录
    user.reset_token = reset_token
    user.reset_token_expires = reset_token_expires
    await db.commit()

    # TODO: 发送重置密码邮件给用户
    # 这里应该集成邮件发送功能

    return {"message": "重置密码链接已发送到您的邮箱"}


@router.post("/reset-password-verify")
async def verify_password_reset(
    reset_data: PasswordResetVerify, db: AsyncSession = Depends(get_db)
):
    # 验证令牌并重置密码
    result = await db.execute(
        select(User).where(
            User.reset_token == reset_data.token,
            User.reset_token_expires > datetime.utcnow(),
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效或已过期的重置链接"
        )

    # 更新密码
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.commit()

    return {"message": "密码重置成功"}
