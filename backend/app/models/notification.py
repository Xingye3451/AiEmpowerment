from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base_class import Base


class Notification(Base):
    """站内信/通知模型"""

    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # system, task, scheduled_task
    status = Column(String, default="unread")  # unread, read

    # 关联的任务ID（可选）
    related_id = Column(String, nullable=True)  # 可以是任务ID、定时任务ID等
    related_type = Column(String, nullable=True)  # 关联对象的类型

    # 创建时间
    created_at = Column(DateTime, default=datetime.now)
    read_at = Column(DateTime, nullable=True)

    # 关联用户
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="notifications", lazy="selectin")

    def __repr__(self):
        return f"<Notification {self.title}>"
