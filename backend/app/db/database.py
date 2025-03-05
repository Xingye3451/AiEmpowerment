from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings
from app.db.base_class import Base
import logging

logger = logging.getLogger(__name__)

# 根据数据库类型设置连接参数
connect_args = {}
if settings.DB_TYPE.lower() == "sqlite":
    # SQLite特有的连接参数
    connect_args = {"check_same_thread": False}
    logger.info("使用SQLite数据库连接参数")

# 异步引擎和会话
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    # 对于MySQL，我们不需要特殊的connect_args
    # 对于SQLite，aiomysql不使用check_same_thread参数
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 同步引擎和会话（用于某些同步操作）
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    connect_args=connect_args if settings.DB_TYPE.lower() == "sqlite" else {},
)
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
