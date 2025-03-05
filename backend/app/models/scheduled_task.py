from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    ForeignKey,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
import uuid
from datetime import datetime


class ScheduledTask(Base):
    """定时任务模型"""

    __tablename__ = "scheduled_tasks"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(
        String(50), nullable=False
    )  # content_distribution, content_collection, data_analysis
    status = Column(
        String(20), nullable=False, default="active"
    )  # active, paused, completed, failed

    # 定时计划
    schedule = Column(
        JSON, nullable=False
    )  # {type: once/daily/weekly/monthly, time: HH:MM:SS, days: [], date: int}

    # 任务数据
    data = Column(JSON, nullable=True)  # 任务相关的数据，如平台、账号、媒体路径等

    # 执行记录
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)

    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="scheduled_tasks", lazy="selectin")

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联的采集任务
    collection_tasks = relationship(
        "CollectionTask", back_populates="scheduled_task", lazy="selectin"
    )

    def __repr__(self):
        return f"<ScheduledTask {self.name}>"
