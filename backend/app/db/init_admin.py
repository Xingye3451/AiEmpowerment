import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.database import engine, AsyncSessionLocal
from app.db.base import Base  # 导入所有模型
from app.models.user import User
from app.core.security import get_password_hash


async def init_db():
    """初始化数据库，删除所有表并重新创建"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表创建成功")


async def create_admin():
    """创建管理员账号"""
    async with AsyncSessionLocal() as db:
        db_session = db
        # 检查是否已存在管理员账号
        result = await db_session.execute(
            User.__table__.select().where(User.username == "admin")
        )
        admin_user = result.scalars().first()

        if admin_user:
            print("管理员账号已存在")
            return

        # 创建管理员账号
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin"),
            is_superuser=True,
            role="admin",
            is_active=True,
        )
        db_session.add(admin_user)
        await db_session.commit()
        print("管理员账号创建成功")


async def ensure_db_exists():
    """确保数据库文件存在"""
    db_path = settings.SYNC_DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))


async def init_all():
    """初始化所有数据库相关操作"""
    await ensure_db_exists()
    await init_db()
    await create_admin()


if __name__ == "__main__":
    asyncio.run(init_all())
