from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


# 视频统计数据模型
class VideoStats(BaseModel):
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0


# 采集视频模型
class CollectedVideoBase(BaseModel):
    platform: str = Field(..., description="平台: douyin, kuaishou, bilibili")
    platform_video_id: str = Field(..., description="平台视频ID")
    title: str = Field(..., description="视频标题")
    description: Optional[str] = Field(None, description="视频描述")
    author: str = Field(..., description="作者名称")
    author_id: Optional[str] = Field(None, description="作者ID")
    thumbnail: Optional[str] = Field(None, description="缩略图URL")
    video_url: Optional[str] = Field(None, description="视频URL")
    duration: Optional[float] = Field(None, description="视频时长（秒）")
    stats: Optional[VideoStats] = Field(None, description="统计数据")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    published_at: Optional[datetime] = Field(None, description="发布时间")


class CollectedVideoCreate(CollectedVideoBase):
    collection_id: Optional[str] = Field(None, description="采集任务ID")


class CollectedVideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    video_url: Optional[str] = None
    local_path: Optional[str] = None
    stats: Optional[VideoStats] = None
    tags: Optional[List[str]] = None
    is_downloaded: Optional[bool] = None
    is_favorite: Optional[bool] = None


class CollectedVideoInDB(CollectedVideoBase):
    id: str
    user_id: int
    collection_id: Optional[str] = None
    local_path: Optional[str] = None
    is_downloaded: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CollectedVideoResponse(CollectedVideoInDB):
    pass


# 采集任务模型
class CollectionTaskBase(BaseModel):
    """采集任务基础模型"""

    name: str
    query: str
    platforms: List[str]
    filters: Optional[Dict[str, Any]] = None


class CollectionTaskCreate(CollectionTaskBase):
    """创建采集任务请求模型"""

    pass


class CollectionTaskUpdate(BaseModel):
    """更新采集任务请求模型"""

    name: Optional[str] = None
    query: Optional[str] = None
    platforms: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None


class CollectionTaskResponse(CollectionTaskBase):
    """采集任务响应模型"""

    id: str
    status: str
    total_found: int = 0
    user_id: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class CollectedContentBase(BaseModel):
    """采集内容基础模型"""

    platform: str
    content_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    author_id: Optional[str] = None
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    duration: Optional[int] = None
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    published_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    local_path: Optional[str] = None
    status: str


class CollectedContentResponse(CollectedContentBase):
    """采集内容响应模型"""

    id: str
    collection_task_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CollectionTaskListResponse(BaseModel):
    """采集任务列表响应模型"""

    total: int
    items: List[CollectionTaskResponse]


class CollectionTaskDetailResponse(BaseModel):
    """采集任务详情响应模型"""

    task: CollectionTaskResponse
    contents: List[CollectedContentResponse]


# 内容标签模型
class ContentTagBase(BaseModel):
    name: str = Field(..., description="标签名称")
    category: Optional[str] = Field(None, description="标签分类")


class ContentTagCreate(ContentTagBase):
    pass


class ContentTagUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    count: Optional[int] = None


class ContentTagInDB(ContentTagBase):
    id: int
    count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ContentTagResponse(ContentTagInDB):
    pass


# 搜索请求模型
class VideoSearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    platform: Optional[str] = Field("douyin", description="平台")
    time_range: Optional[str] = Field(
        "today", description="时间范围: today, week, month, all"
    )
    sort_by: Optional[str] = Field(
        "likes", description="排序方式: likes, views, comments, shares, date"
    )
    min_likes: Optional[int] = Field(None, description="最小点赞数")
    min_views: Optional[int] = Field(None, description="最小播放量")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    page: Optional[int] = Field(1, description="页码")
    per_page: Optional[int] = Field(10, description="每页数量")


# 下载请求模型
class VideoDownloadRequest(BaseModel):
    video_id: str = Field(..., description="视频ID")
    platform: str = Field(..., description="平台")
