from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    ForeignKey,
    Boolean,
    Float,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
import uuid
from datetime import datetime


class CollectedVideo(Base):
    """采集的视频内容模型"""

    __tablename__ = "collected_videos"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    platform = Column(String(50), nullable=False)  # douyin, kuaishou, bilibili
    platform_video_id = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    author = Column(String(255), nullable=False)
    author_id = Column(String(255), nullable=True)

    # 媒体信息
    thumbnail = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=True)  # 本地存储路径
    duration = Column(Float, nullable=True)

    # 统计数据
    stats = Column(JSON, nullable=True)  # {likes, comments, shares, views}

    # 标签和分类
    tags = Column(JSON, nullable=True)  # 标签列表

    # 采集信息
    collection_id = Column(String(36), ForeignKey("collection_tasks.id"), nullable=True)
    collection = relationship(
        "CollectionTask", back_populates="videos", lazy="selectin"
    )

    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="collected_videos", lazy="selectin")

    # 状态
    is_downloaded = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)

    # 平台发布时间
    published_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<CollectedVideo {self.title}>"


class CollectionTask(Base):
    """内容采集任务模型"""

    __tablename__ = "collection_tasks"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    query = Column(String, nullable=False)  # 搜索关键词
    platforms = Column(
        JSON, nullable=False
    )  # 平台列表，如 ["douyin", "kuaishou", "bilibili"]
    filters = Column(JSON, nullable=True)  # 过滤条件
    status = Column(String, default="pending")  # pending, running, completed, failed
    total_found = Column(Integer, default=0)  # 找到的内容数量

    # 任务执行时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 关联用户
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="collection_tasks", lazy="selectin")

    # 关联定时任务（如果是由定时任务触发的）
    scheduled_task_id = Column(String, ForeignKey("scheduled_tasks.id"), nullable=True)
    scheduled_task = relationship(
        "ScheduledTask", back_populates="collection_tasks", lazy="selectin"
    )

    # 关联采集到的内容
    collected_contents = relationship(
        "CollectedContent", back_populates="collection_task", lazy="selectin"
    )
    videos = relationship(
        "CollectedVideo", back_populates="collection", lazy="selectin"
    )

    def __repr__(self):
        return f"<CollectionTask {self.name}>"


class CollectedContent(Base):
    """采集到的内容模型"""

    __tablename__ = "collected_contents"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String, nullable=False)  # 平台名称
    content_id = Column(String, nullable=False)  # 平台上的内容ID
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    author_id = Column(String, nullable=True)
    url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)  # 视频时长（秒）
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    views = Column(Integer, default=0)
    published_at = Column(DateTime, nullable=True)

    # 额外数据，如标签、分类等
    meta_data = Column(JSON, nullable=True)

    # 本地存储路径
    local_path = Column(String, nullable=True)

    # 内容状态
    status = Column(
        String, default="collected"
    )  # collected, downloaded, processed, distributed

    # 创建时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联采集任务
    collection_task_id = Column(
        String, ForeignKey("collection_tasks.id"), nullable=False
    )
    collection_task = relationship(
        "CollectionTask", back_populates="collected_contents", lazy="selectin"
    )

    # 关联用户
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="collected_contents", lazy="selectin")

    def __repr__(self):
        return f"<CollectedContent {self.title}>"


class ContentTag(Base):
    """内容标签模型"""

    __tablename__ = "content_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    category = Column(String(50), nullable=True)
    count = Column(Integer, default=0)  # 使用次数

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ContentTag {self.name}>"
