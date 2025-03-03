from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from app.core.config import settings

# 异步引擎和会话
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 同步引擎和会话（用于某些同步操作）
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()