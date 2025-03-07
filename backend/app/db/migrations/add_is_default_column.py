"""
向ai_service_configs表添加缺失的列的迁移脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录添加到 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(backend_dir))

from app.db.database import engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def add_is_default_column():
    """向ai_service_configs表添加缺失的列"""
    # 检查列是否已存在
    async with engine.begin() as conn:
        # 检查表是否存在
        result = await conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_service_configs'"
            )
        )
        if not result.scalar():
            print("ai_service_configs表不存在，跳过添加列")
            return

        # 检查列是否存在
        result = await conn.execute(text("PRAGMA table_info(ai_service_configs)"))
        columns = result.fetchall()
        column_names = [column[1] for column in columns]

        # 添加缺失的列
        missing_columns = {
            "is_default": "BOOLEAN DEFAULT FALSE",
            "priority": "INTEGER DEFAULT 0",
            "timeout": "INTEGER DEFAULT 60",
            "failure_count": "INTEGER DEFAULT 0",
            "advanced_params": "JSON",
            "auto_detect": "BOOLEAN",
            "language": "VARCHAR",
            "quality": "VARCHAR",
            "model_type": "VARCHAR",
            "batch_size": "INTEGER",
            "smooth": "BOOLEAN",
        }

        for column_name, column_type in missing_columns.items():
            if column_name not in column_names:
                try:
                    await conn.execute(
                        text(
                            f"ALTER TABLE ai_service_configs ADD COLUMN {column_name} {column_type}"
                        )
                    )
                    print(f"成功添加{column_name}列到ai_service_configs表")
                except Exception as e:
                    print(f"添加{column_name}列时出错: {e}")
            else:
                print(f"{column_name}列已存在于ai_service_configs表中")


if __name__ == "__main__":
    asyncio.run(add_is_default_column())
