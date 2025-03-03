import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录添加到 Python 路径中
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from app.db.database import Base, engine, AsyncSession
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully.")

async def create_admin():
    """创建管理员账号"""
    async with AsyncSession(engine) as session:
        # 检查管理员是否已存在
        result = await session.execute(
            "SELECT * FROM users WHERE username = 'admin'"
        )
        admin = result.first()
        
        if not admin:
            admin_user = User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("admin123456"),
                is_active=True,
                role="admin"
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
        open(settings.DB_FILE, 'a').close()
        print(f"Created database file at {settings.DB_FILE}")

async def init_all():
    """执行所有初始化步骤"""
    ensure_db_exists()
    await init_db()
    await create_admin()

if __name__ == "__main__":
    asyncio.run(init_all())