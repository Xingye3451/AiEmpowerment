import sys
import os
import asyncio
from pathlib import Path
from sqlalchemy import text, select

# 将项目根目录添加到 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from app.db.database import Base, engine, AsyncSession
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.task import Task
from app.models.social_account import (
    SocialAccount,
    AccountGroup,
    SocialPost,
    DistributionTask,
    account_group_association,
)
from app.models.notification import Notification
from app.models.comfyui import ComfyUIWorkflow
from app.models.scheduled_task import ScheduledTask
from app.models.content_collection import (
    CollectionTask,
    CollectedContent,
    CollectedVideo,
)


async def init_db():
    """初始化数据库表"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("Database tables created successfully.")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        import traceback

        traceback.print_exc()
        raise


async def create_admin():
    """创建管理员账号"""
    async with AsyncSession(engine) as session:
        # 使用 SQLAlchemy ORM 查询语法替代原始 SQL
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalars().first()

        if not admin:
            admin_user = User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("admin123456"),
                is_active=True,
                role="admin",
            )
            session.add(admin_user)
            await session.commit()
            print("Administrator account created successfully")
        else:
            print("Administrator account already exists")


def ensure_db_exists():
    """确保数据库文件存在"""
    db_dir = os.path.dirname(os.path.abspath(settings.DB_FILE))
    os.makedirs(db_dir, exist_ok=True)
    if not os.path.exists(settings.DB_FILE):
        open(settings.DB_FILE, "a").close()
        print(f"Created database file at {settings.DB_FILE}")


async def init_social_account_tables():
    """初始化社交账号相关的数据库表"""
    async with engine.begin() as conn:
        # 创建社交账号相关表
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                SocialAccount.__table__,
                AccountGroup.__table__,
                account_group_association,
                SocialPost.__table__,
                DistributionTask.__table__,
            ],
        )
        print("Social account tables created successfully.")


async def init_task_tables():
    """初始化任务相关的数据库表"""
    async with engine.begin() as conn:
        # 创建任务相关表
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                Task.__table__,
                ScheduledTask.__table__,
                CollectionTask.__table__,
            ],
        )
        print("Task tables created successfully.")


async def init_notification_tables():
    """初始化通知相关的数据库表"""
    async with engine.begin() as conn:
        # 创建通知相关表
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                Notification.__table__,
            ],
        )
        print("Notification tables created successfully.")


async def init_content_collection_tables():
    """初始化内容收集相关的数据库表"""
    async with engine.begin() as conn:
        # 创建内容收集相关表
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                CollectedContent.__table__,
                CollectedVideo.__table__,
            ],
        )
        print("Content collection tables created successfully.")


async def init_comfyui_tables():
    """初始化ComfyUI相关的数据库表"""
    async with engine.begin() as conn:
        # 创建ComfyUI相关表
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                ComfyUIWorkflow.__table__,
            ],
        )
        print("ComfyUI tables created successfully.")


async def init_all():
    """执行所有初始化步骤"""
    # 1. 确保数据库文件存在
    ensure_db_exists()

    # 2. 初始化数据库表结构
    await init_db()

    # 3. 创建管理员账号
    await create_admin()

    # 4. 初始化社交账号相关表
    await init_social_account_tables()

    # 5. 初始化任务相关表
    await init_task_tables()

    # 6. 初始化通知相关表
    await init_notification_tables()

    # 7. 初始化内容收集相关表
    await init_content_collection_tables()

    # 8. 初始化ComfyUI相关表
    await init_comfyui_tables()

    print("Database initialization completed.")


if __name__ == "__main__":
    asyncio.run(init_all())
