from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login/admin")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == token_data.username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # 检查用户是否被禁用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    """
    验证当前用户是否处于活跃状态
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_current_admin(
    token: str = Depends(admin_oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="管理员权限验证失败",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None or role != "admin":
            raise credentials_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == token_data.username))
    user = result.scalar_one_or_none()

    if user is None or user.role != "admin":
        raise credentials_exception
    return user


async def get_current_active_superuser(
    token: str = Depends(admin_oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """
    验证当前用户是否为超级管理员
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="超级管理员权限验证失败",
        headers={"WWW-Authenticate": "Bearer"},
    )
    permission_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="权限不足，需要超级管理员权限",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None or role != "admin":
            raise credentials_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == token_data.username))
    user = result.scalar_one_or_none()

    if user is None or user.role != "admin":
        raise credentials_exception

    # 检查是否为超级管理员
    if not user.is_superuser:
        raise permission_exception

    return user
