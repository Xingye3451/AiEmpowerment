from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any
from app.core.deps import get_db, get_current_admin
from app.models.user import User
from app.schemas.user import UserCreate, User as UserSchema, UserUpdate
from app.core.security import get_password_hash, verify_password

router = APIRouter()


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

    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role="user",
        is_active=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"msg": "用户创建成功"}


@router.delete("/users/{user_id}", response_model=Dict[str, str])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """删除用户（仅管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账号")

    await db.delete(user)
    await db.commit()
    return {"msg": "用户删除成功"}


@router.put("/users/{user_id}/reset-password", response_model=Dict[str, str])
async def reset_user_password(
    user_id: int,
    reset_data: dict,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """重置用户密码（仅管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_password = reset_data.get("new_password")
    if not new_password:
        raise HTTPException(status_code=400, detail="新密码不能为空")

    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    return {"msg": "密码重置成功"}


@router.put("/users/{user_id}/toggle-status", response_model=Dict[str, str])
async def toggle_user_status(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """切换用户状态（启用/禁用）（仅管理员）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="不能修改管理员状态")

    user.is_active = not user.is_active
    await db.commit()
    return {"msg": f"用户状态已更改为{'启用' if user.is_active else '禁用'}"}


@router.put("/users/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: int,
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
    old_password = password_data.get("old_password")
    new_password = password_data.get("new_password")

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="旧密码和新密码都不能为空")

    if not verify_password(old_password, current_admin.hashed_password):
        raise HTTPException(status_code=400, detail="旧密码不正确")

    current_admin.hashed_password = get_password_hash(new_password)
    await db.commit()
    return {"msg": "密码修改成功"}
