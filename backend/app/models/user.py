from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.db.base_class import Base
from app.models.social_account import SocialAccount
from app.models.notification import Notification
from app.models.scheduled_task import ScheduledTask
from app.models.comfyui import ComfyUIWorkflow
from app.models.content_collection import (
    CollectedVideo,
    CollectionTask,
    CollectedContent,
)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="user")  # user, admin
    last_login = Column(DateTime, nullable=True)
    last_active = Column(DateTime, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 新增关联关系 - 使用字符串引用避免循环导入
    social_accounts = relationship(
        "SocialAccount", back_populates="user", lazy="selectin"
    )
    account_groups = relationship(
        "AccountGroup", back_populates="user", lazy="selectin"
    )
    social_posts = relationship("SocialPost", back_populates="user", lazy="selectin")
    distribution_tasks = relationship(
        "DistributionTask", back_populates="user", lazy="selectin"
    )
    comfyui_workflows = relationship(
        "ComfyUIWorkflow", back_populates="user", lazy="selectin"
    )
    notifications = relationship("Notification", back_populates="user", lazy="selectin")

    # 添加新的关联关系
    scheduled_tasks = relationship(
        "ScheduledTask", back_populates="user", lazy="selectin"
    )
    collection_tasks = relationship(
        "CollectionTask", back_populates="user", lazy="selectin"
    )
    collected_contents = relationship(
        "CollectedContent", back_populates="user", lazy="selectin"
    )
    collected_videos = relationship(
        "CollectedVideo", back_populates="user", lazy="selectin"
    )
    tasks = relationship("Task", back_populates="user", lazy="selectin")

    # 以下字段已弃用，保留是为了向后兼容
    douyin_accounts = Column(JSON, nullable=True)  # 已弃用，使用social_accounts替代
    douyin_groups = Column(JSON, nullable=True)  # 已弃用，使用account_groups替代

    def __repr__(self):
        return f"<User {self.username}>"
