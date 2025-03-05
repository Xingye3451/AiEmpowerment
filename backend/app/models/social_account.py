from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    JSON,
    DateTime,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from datetime import datetime
import uuid

# 账号和分组的多对多关系表
account_group_association = Table(
    "account_group_association",
    Base.metadata,
    Column("account_id", Integer, ForeignKey("social_accounts.id")),
    Column("group_id", Integer, ForeignKey("account_groups.id")),
)


class SocialAccount(Base):
    """社交媒体账号模型"""

    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    password = Column(String)
    platform = Column(String, index=True)  # 平台类型：douyin, kuaishou, bilibili等
    status = Column(String, default="inactive")  # 状态：active, inactive
    cookies = Column(JSON, nullable=True)  # 存储登录后的cookies
    extra_data = Column(JSON, nullable=True)  # 存储额外的平台特定数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # 关联关系
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="social_accounts", lazy="selectin")
    groups = relationship(
        "AccountGroup",
        secondary=account_group_association,
        back_populates="accounts",
        lazy="selectin",
    )
    posts = relationship("SocialPost", back_populates="account", lazy="selectin")

    def __repr__(self):
        return f"<SocialAccount {self.username} ({self.platform})>"


class AccountGroup(Base):
    """账号分组模型"""

    __tablename__ = "account_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="account_groups", lazy="selectin")
    accounts = relationship(
        "SocialAccount",
        secondary=account_group_association,
        back_populates="groups",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<AccountGroup {self.name}>"


class SocialPost(Base):
    """社交媒体发布记录模型"""

    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    description = Column(String, nullable=True)
    media_path = Column(String)  # 视频或图片路径
    status = Column(String, default="pending")  # 状态：pending, published, failed
    result = Column(JSON, nullable=True)  # 发布结果
    scheduled_time = Column(DateTime, nullable=True)  # 计划发布时间
    published_time = Column(DateTime, nullable=True)  # 实际发布时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="social_posts", lazy="selectin")
    account_id = Column(Integer, ForeignKey("social_accounts.id"))
    account = relationship("SocialAccount", back_populates="posts", lazy="selectin")
    task_id = Column(String, nullable=True)  # 关联的任务ID

    def __repr__(self):
        return f"<SocialPost {self.title}>"


class DistributionTask(Base):
    """内容分发任务模型"""

    __tablename__ = "distribution_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    description = Column(String, nullable=True)
    media_path = Column(String)  # 视频或图片路径
    platforms = Column(JSON)  # 目标平台列表
    accounts = Column(JSON)  # 目标账号列表
    status = Column(
        String, default="pending"
    )  # 状态：pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 进度百分比
    result = Column(JSON, nullable=True)  # 分发结果
    scheduled_time = Column(DateTime, nullable=True)  # 计划分发时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="distribution_tasks", lazy="selectin")

    def __repr__(self):
        return f"<DistributionTask {self.title}>"
