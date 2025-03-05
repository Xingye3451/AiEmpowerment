from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db, get_current_active_user, get_current_active_superuser
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, User as UserSchema
from app.core.security import get_password_hash

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    获取所有用户列表，仅限超级管理员访问
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.get("/me", response_model=UserSchema)
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    """
    获取当前登录用户信息
    """
    return current_user


@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    根据ID获取用户信息，仅限超级管理员访问
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/", response_model=UserSchema)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    创建新用户，仅限超级管理员访问
    """
    result = await db.execute(select(User).filter(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="该邮箱已被注册",
        )

    result = await db.execute(select(User).filter(User.username == user_in.username))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="该用户名已被使用",
        )

    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    更新用户信息，仅限超级管理员访问
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )

    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    删除用户，仅限超级管理员访问
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )

    await db.delete(user)
    await db.commit()
    return user
