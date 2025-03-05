from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ScheduleBase(BaseModel):
    type: str = Field(..., description="计划类型: once, daily, weekly, monthly")
    time: str = Field(..., description="执行时间，格式为HH:MM:SS")
    days: Optional[List[str]] = Field(
        None, description="每周执行的星期几，如['monday', 'friday']"
    )
    date: Optional[int] = Field(None, description="每月执行的日期，如1-31")


class ScheduledTaskBase(BaseModel):
    """定时任务基础模型"""

    name: str
    type: str  # content_collection, content_distribution, data_analysis
    schedule: Dict[str, Any]  # 调度信息
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ScheduledTaskCreate(ScheduledTaskBase):
    """创建定时任务请求模型"""

    pass


class ScheduledTaskUpdate(BaseModel):
    """更新定时任务请求模型"""

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None


class ScheduledTaskInDB(ScheduledTaskBase):
    id: str
    status: str
    user_id: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ScheduledTaskResponse(ScheduledTaskBase):
    """定时任务响应模型"""

    id: str
    status: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None

    class Config:
        orm_mode = True


class ScheduledTaskListResponse(BaseModel):
    """定时任务列表响应模型"""

    total: int
    items: List[ScheduledTaskResponse]
