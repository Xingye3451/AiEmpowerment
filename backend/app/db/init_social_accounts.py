import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录添加到 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from app.db.database import Base, engine, AsyncSession
from app.models.social_account import (
    SocialAccount,
    AccountGroup,
    SocialPost,
    DistributionTask,
    account_group_association,
)
from app.core.config import settings


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


async def create_default_platforms():
    """创建默认的平台数据"""
    # 这里可以添加默认平台数据的创建逻辑
    # 目前平台数据是通过API直接返回的，不需要存储在数据库中
    pass


async def init_all():
    """执行所有初始化步骤"""
    # 初始化社交账号相关表
    await init_social_account_tables()

    # 创建默认平台数据
    await create_default_platforms()

    print("Social account initialization completed.")


if __name__ == "__main__":
    asyncio.run(init_all())
