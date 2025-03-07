"""
创建ai_service_configs表的数据库迁移脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录添加到 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(backend_dir))

from app.db.database import engine
from app.models.ai_config import AIServiceConfig
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession


async def create_ai_service_configs_table():
    """创建ai_service_configs表"""
    # 检查表是否已存在
    async with engine.begin() as conn:
        # 使用run_sync来在同步上下文中执行inspect
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )

        if "ai_service_configs" not in tables:
            # 创建ai_service_configs表
            await conn.run_sync(lambda conn: AIServiceConfig.__table__.create(conn))
            print("ai_service_configs表创建成功")
        else:
            print("ai_service_configs表已存在，尝试更新表结构")

            # 获取表中现有的列
            result = await conn.execute(text("PRAGMA table_info(ai_service_configs)"))
            columns = result.fetchall()
            column_names = [column[1] for column in columns]

            # 检查并添加缺失的列
            expected_columns = {
                "id": "INTEGER PRIMARY KEY",
                "service_type": "VARCHAR",
                "service_name": "VARCHAR NOT NULL",
                "service_url": "VARCHAR NOT NULL",
                "is_active": "BOOLEAN DEFAULT TRUE",
                "is_default": "BOOLEAN DEFAULT FALSE",
                "priority": "INTEGER DEFAULT 0",
                "timeout": "INTEGER DEFAULT 60",
                "failure_count": "INTEGER DEFAULT 0",
                "advanced_params": "JSON",
                "created_at": "DATETIME",
                "updated_at": "DATETIME",
                "auto_detect": "BOOLEAN",
                "language": "VARCHAR",
                "quality": "VARCHAR",
                "model_type": "VARCHAR",
                "batch_size": "INTEGER",
                "smooth": "BOOLEAN",
            }

            for column_name, column_type in expected_columns.items():
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


if __name__ == "__main__":
    asyncio.run(create_ai_service_configs_table())
