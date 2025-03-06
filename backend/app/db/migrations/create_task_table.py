"""
创建任务表的数据库迁移脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录添加到 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(backend_dir))

from app.db.database import engine
from app.models.task import Task
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession


async def create_task_table():
    """创建任务表"""
    # 检查表是否已存在
    async with engine.begin() as conn:
        # 使用run_sync来在同步上下文中执行inspect
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )

        if "tasks" not in tables:
            # 创建任务表
            await conn.run_sync(lambda conn: Task.__table__.create(conn))
            print("任务表创建成功")
        else:
            print("任务表已存在")


if __name__ == "__main__":
    asyncio.run(create_task_table())
