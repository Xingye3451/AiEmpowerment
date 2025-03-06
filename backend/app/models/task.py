from sqlalchemy import Column, String, DateTime, Integer, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.base_class import Base


class Task(Base):
    """任务模型，用于持久化存储任务信息"""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(
        String, nullable=False
    )  # 任务类型：video_processing, douyin_post 等
    status = Column(
        String, nullable=False
    )  # 任务状态：pending, scheduled, running, completed, failed, retrying
    progress = Column(Integer, default=0)  # 任务进度：0-100
    result = Column(JSON, nullable=True)  # 任务结果，JSON格式
    error = Column(Text, nullable=True)  # 错误信息
    data = Column(JSON, nullable=False)  # 任务数据，JSON格式
    retry_count = Column(Integer, default=0)  # 重试次数
    max_retries = Column(Integer, default=3)  # 最大重试次数

    # 时间相关
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    scheduled_at = Column(DateTime, nullable=True)  # 计划执行时间
    last_retry_at = Column(DateTime, nullable=True)  # 上次重试时间

    # 关联用户
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.id}>"
