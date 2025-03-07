"""
运行所有数据库迁移脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录添加到 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(backend_dir))

from app.db.migrations.create_task_table import create_task_table
from app.db.migrations.create_ai_service_configs_table import (
    create_ai_service_configs_table,
)
from sqlalchemy.ext.asyncio import AsyncSession


async def run_all_migrations():
    """运行所有迁移脚本"""
    print("开始运行数据库迁移...")

    # 创建任务表
    await create_task_table()

    # 创建或更新ai_service_configs表
    await create_ai_service_configs_table()

    print("数据库迁移完成")


if __name__ == "__main__":
    asyncio.run(run_all_migrations())
