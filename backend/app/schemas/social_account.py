from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class SocialAccountBase(BaseModel):
    username: str
    platform: str
    status: Optional[str] = "inactive"


class SocialAccountCreate(SocialAccountBase):
    password: str
    extra_data: Optional[Dict[str, Any]] = None


class SocialAccountUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class SocialAccountResponse(SocialAccountBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AccountGroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class AccountGroupCreate(AccountGroupBase):
    account_ids: Optional[List[int]] = None


class AccountGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    account_ids: Optional[List[int]] = None


class AccountGroupResponse(AccountGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    accounts: List[SocialAccountResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SocialPostBase(BaseModel):
    title: str
    description: Optional[str] = None
    media_path: str
    scheduled_time: Optional[datetime] = None


class SocialPostCreate(SocialPostBase):
    account_id: int


class SocialPostUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class SocialPostResponse(SocialPostBase):
    id: int
    post_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    published_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    account: SocialAccountResponse

    model_config = ConfigDict(from_attributes=True)


class DistributionTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    media_path: str
    platforms: List[str]
    scheduled_time: Optional[datetime] = None


class DistributionTaskCreate(DistributionTaskBase):
    account_ids: List[int]


class DistributionTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None


class DistributionTaskResponse(DistributionTaskBase):
    id: int
    task_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    accounts: List[SocialAccountResponse] = []

    model_config = ConfigDict(from_attributes=True)


# 批量操作相关Schema
class BatchLoginRequest(BaseModel):
    accounts: List[SocialAccountCreate]


class LoginResult(BaseModel):
    username: str
    platform: str
    success: bool
    error: Optional[str] = None


class BatchLoginResponse(BaseModel):
    results: List[LoginResult]


class BatchPostRequest(BaseModel):
    account_ids: List[int]
    title: str
    description: Optional[str] = None
    media_path: str
    scheduled_time: Optional[datetime] = None


class PostResult(BaseModel):
    account_id: int
    username: str
    platform: str
    success: bool
    post_id: Optional[str] = None
    error: Optional[str] = None


class BatchPostResponse(BaseModel):
    results: List[PostResult]
    task_id: str
