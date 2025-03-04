import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录添加到 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from app.db.database import engine, AsyncSession, Base
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings
from sqlalchemy import text

async def init_db():
    """初始化数据库表结构"""
    async with engine.begin() as conn:
        # 先删除所有表，确保是全新的状态
        await conn.run_sync(Base.metadata.drop_all)
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        print("数据库表创建成功")

async def create_admin():
    """创建管理员账号"""
    try:
        # 先确保数据库表存在
        await init_db()
        
        async with AsyncSession(engine) as session:
            # 检查管理员是否已存在
            result = await session.execute(
                text("SELECT * FROM users WHERE username = 'admin'")
            )
            admin = result.first()
            
            if not admin:
                # 创建管理员用户
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash("admin123456"),
                    role="admin",
                    is_active=True
                )
                session.add(admin_user)
                await session.commit()
                print("管理员账号创建成功！")
                print("用户名: admin")
                print("密码: admin123456")
            else:
                print("管理员账号已存在")
                
    except Exception as e:
        print(f"创建管理员账号时出错: {e}")
        raise

def ensure_db_exists():
    """确保数据库文件存在"""
    db_dir = os.path.dirname(os.path.abspath(settings.DB_FILE))
    os.makedirs(db_dir, exist_ok=True)
    if not os.path.exists(settings.DB_FILE):
        open(settings.DB_FILE, 'a').close()
        print(f"Created database file at {settings.DB_FILE}")

async def init_all():
    """执行所有初始化步骤"""
    ensure_db_exists()
    await create_admin()

if __name__ == "__main__":
    asyncio.run(init_all())