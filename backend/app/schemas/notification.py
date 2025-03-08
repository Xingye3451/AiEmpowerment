from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class NotificationBase(BaseModel):
    """通知基础模型"""

    title: str
    content: str
    type: str  # system, task, scheduled_task
    related_id: Optional[str] = None
    related_type: Optional[str] = None


class NotificationCreate(NotificationBase):
    """创建通知请求模型"""

    user_id: str


class NotificationUpdate(BaseModel):
    """更新通知请求模型"""

    status: Optional[str] = None
    read_at: Optional[datetime] = None


class NotificationResponse(NotificationBase):
    """通知响应模型"""

    id: str
    status: str
    user_id: str
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """通知列表响应模型"""

    total: int
    unread_count: int
    items: List[NotificationResponse]


class NotificationCountResponse(BaseModel):
    """通知计数响应模型"""

    total: int
    unread: int
