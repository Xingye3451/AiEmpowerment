from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class TaskBase(BaseModel):
    """任务基础模型"""

    task_type: str
    data: Dict[str, Any]
    user_id: Optional[str] = None


class TaskCreate(TaskBase):
    """创建任务请求模型"""

    scheduled_at: Optional[datetime] = None
    max_retries: Optional[int] = 3


class TaskUpdate(BaseModel):
    """更新任务请求模型"""

    status: Optional[str] = None
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class TaskInDB(TaskBase):
    """数据库中的任务模型"""

    id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int
    max_retries: int
    created_at: datetime
    updated_at: datetime
    scheduled_at: Optional[datetime] = None
    last_retry_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class TaskResponse(TaskInDB):
    """任务响应模型"""

    pass


class TaskListResponse(BaseModel):
    """任务列表响应模型"""

    total: int
    items: List[TaskResponse]
