from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: str  # Changed from EmailStr to str
    model_config = ConfigDict(from_attributes=True)  # 新版pydantic配置


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None  # Changed from EmailStr to str
    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    id: str
    is_active: bool
    role: str
    last_login: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class DouyinAccount(BaseModel):
    username: str
    password: str


class DouyinVideo(BaseModel):
    title: str
    file_path: str
    description: Optional[str] = None


class BatchDouyinLogin(BaseModel):
    accounts: List[DouyinAccount]


class BatchDouyinPost(BaseModel):
    accounts: List[str]  # 抖音用户名列表
    video: DouyinVideo


class DouyinLoginResponse(BaseModel):
    username: str
    success: bool
    error: Optional[str] = None


class BatchDouyinLoginResponse(BaseModel):
    results: List[DouyinLoginResponse]


class DouyinPostResponse(BaseModel):
    username: str
    success: bool
    video_id: Optional[str] = None
    error: Optional[str] = None


class BatchDouyinPostResponse(BaseModel):
    results: List[DouyinPostResponse]


class DouyinGroup(BaseModel):
    name: str
    accounts: List[str]


class DouyinPostHistory(BaseModel):
    video_id: str
    title: str
    description: Optional[str]
    accounts: List[str]
    success_count: int
    failed_count: int
    created_at: datetime
    retries: int = 0
    status: str


class ScheduledPost(BaseModel):
    video_path: str
    title: str
    description: Optional[str]
    accounts: List[str]
    schedule_time: datetime
    group_id: Optional[str]


class DouyinStats(BaseModel):
    total_posts: int
    success_rate: float
    account_stats: Dict[str, Dict[str, int]]


class PasswordReset(BaseModel):
    email: str  # Changed from EmailStr to str


class PasswordResetVerify(BaseModel):
    token: str
    new_password: str
