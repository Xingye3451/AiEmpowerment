from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Response,
    Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
import uuid
import logging

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.social_account import (
    SocialAccount,
    AccountGroup,
    SocialPost,
    DistributionTask,
)
from app.schemas.social_account import (
    SocialAccountCreate,
    SocialAccountUpdate,
    SocialAccountResponse,
    AccountGroupCreate,
    AccountGroupUpdate,
    AccountGroupResponse,
    SocialPostCreate,
    SocialPostUpdate,
    SocialPostResponse,
    DistributionTaskCreate,
    DistributionTaskUpdate,
    DistributionTaskResponse,
    BatchLoginRequest,
    BatchLoginResponse,
    LoginResult,
    BatchPostRequest,
    BatchPostResponse,
    PostResult,
)
from app.core.task_queue import TaskQueue, Task, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter()
task_queue = TaskQueue()


# 社交账号相关路由
@router.post("/accounts", response_model=SocialAccountResponse)
async def create_social_account(
    account: SocialAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新的社交媒体账号"""
    new_account = SocialAccount(
        username=account.username,
        password=account.password,
        platform=account.platform,
        status=account.status,
        extra_data=account.extra_data,
        user_id=current_user.id,
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


@router.get("/accounts", response_model=List[SocialAccountResponse])
async def get_social_accounts(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的社交媒体账号列表"""
    query = db.query(SocialAccount).filter(SocialAccount.user_id == current_user.id)

    if platform:
        query = query.filter(SocialAccount.platform == platform)

    if status:
        query = query.filter(SocialAccount.status == status)

    accounts = query.all()
    return accounts


@router.get("/accounts/{account_id}", response_model=SocialAccountResponse)
async def get_social_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取特定社交媒体账号的详情"""
    account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.id == account_id, SocialAccount.user_id == current_user.id
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    return account


@router.put("/accounts/{account_id}", response_model=SocialAccountResponse)
async def update_social_account(
    account_id: int,
    account_update: SocialAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新社交媒体账号信息"""
    account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.id == account_id, SocialAccount.user_id == current_user.id
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    update_data = account_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(account, key, value)

    account.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}")
async def delete_social_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除社交媒体账号"""
    account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.id == account_id, SocialAccount.user_id == current_user.id
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    db.delete(account)
    db.commit()
    return {"message": "账号已删除"}


# 账号分组相关路由
@router.post("/groups", response_model=AccountGroupResponse)
async def create_account_group(
    group: AccountGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新的账号分组"""
    new_group = AccountGroup(
        name=group.name, description=group.description, user_id=current_user.id
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # 如果提供了账号ID列表，添加账号到分组
    if group.account_ids:
        accounts = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.id.in_(group.account_ids),
                SocialAccount.user_id == current_user.id,
            )
            .all()
        )

        new_group.accounts = accounts
        db.commit()
        db.refresh(new_group)

    return new_group


@router.get("/groups", response_model=List[AccountGroupResponse])
async def get_account_groups(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取当前用户的账号分组列表"""
    groups = (
        db.query(AccountGroup).filter(AccountGroup.user_id == current_user.id).all()
    )
    return groups


@router.get("/groups/{group_id}", response_model=AccountGroupResponse)
async def get_account_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取特定账号分组的详情"""
    group = (
        db.query(AccountGroup)
        .filter(AccountGroup.id == group_id, AccountGroup.user_id == current_user.id)
        .first()
    )

    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    return group


@router.put("/groups/{group_id}", response_model=AccountGroupResponse)
async def update_account_group(
    group_id: int,
    group_update: AccountGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新账号分组信息"""
    group = (
        db.query(AccountGroup)
        .filter(AccountGroup.id == group_id, AccountGroup.user_id == current_user.id)
        .first()
    )

    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 更新基本信息
    if group_update.name is not None:
        group.name = group_update.name

    if group_update.description is not None:
        group.description = group_update.description

    # 更新关联的账号
    if group_update.account_ids is not None:
        accounts = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.id.in_(group_update.account_ids),
                SocialAccount.user_id == current_user.id,
            )
            .all()
        )

        group.accounts = accounts

    group.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(group)
    return group


@router.delete("/groups/{group_id}")
async def delete_account_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除账号分组"""
    group = (
        db.query(AccountGroup)
        .filter(AccountGroup.id == group_id, AccountGroup.user_id == current_user.id)
        .first()
    )

    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    db.delete(group)
    db.commit()
    return {"message": "分组已删除"}


# 批量操作相关路由
@router.post("/batch-login", response_model=BatchLoginResponse)
async def batch_login(
    login_data: BatchLoginRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量登录社交媒体账号"""
    results = []

    for account_data in login_data.accounts:
        try:
            # 检查账号是否已存在
            existing_account = (
                db.query(SocialAccount)
                .filter(
                    SocialAccount.username == account_data.username,
                    SocialAccount.platform == account_data.platform,
                    SocialAccount.user_id == current_user.id,
                )
                .first()
            )

            if existing_account:
                # 更新现有账号
                existing_account.password = account_data.password
                existing_account.status = "active"
                existing_account.last_login = datetime.utcnow()
                existing_account.updated_at = datetime.utcnow()
                account = existing_account
            else:
                # 创建新账号
                account = SocialAccount(
                    username=account_data.username,
                    password=account_data.password,
                    platform=account_data.platform,
                    status="active",
                    extra_data=account_data.extra_data,
                    user_id=current_user.id,
                    last_login=datetime.utcnow(),
                )
                db.add(account)

            # 这里应该有实际的登录逻辑，根据不同平台调用不同的API
            # 目前简化处理，假设登录成功
            success = True
            error = None

            # 如果登录成功，更新cookies和状态
            if success:
                account.cookies = {"session_id": str(uuid.uuid4())}  # 模拟cookies
            else:
                account.status = "inactive"
                error = "登录失败"

            results.append(
                LoginResult(
                    username=account.username,
                    platform=account.platform,
                    success=success,
                    error=error,
                )
            )

        except Exception as e:
            logger.error(f"账号登录失败: {str(e)}")
            results.append(
                LoginResult(
                    username=account_data.username,
                    platform=account_data.platform,
                    success=False,
                    error=str(e),
                )
            )

    db.commit()
    return BatchLoginResponse(results=results)


@router.post("/batch-post", response_model=BatchPostResponse)
async def batch_post(
    post_data: BatchPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量发布内容到多个社交媒体账号"""
    # 检查媒体文件是否存在
    if not os.path.exists(post_data.media_path):
        raise HTTPException(status_code=400, detail="媒体文件不存在")

    # 获取指定的账号
    accounts = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.id.in_(post_data.account_ids),
            SocialAccount.user_id == current_user.id,
        )
        .all()
    )

    if not accounts:
        raise HTTPException(status_code=400, detail="未找到有效账号")

    # 创建分发任务
    task_id = str(uuid.uuid4())

    # 准备任务数据
    account_data = []
    for account in accounts:
        account_data.append(
            {
                "id": account.id,
                "username": account.username,
                "platform": account.platform,
            }
        )

    # 创建任务
    task = Task(
        task_id=task_id,
        task_type="social_post",
        data={
            "accounts": account_data,
            "media_info": {
                "path": post_data.media_path,
                "title": post_data.title,
                "description": post_data.description,
            },
            "user_id": current_user.id,
            "scheduled_time": (
                post_data.scheduled_time.isoformat()
                if post_data.scheduled_time
                else None
            ),
        },
    )

    # 添加任务到队列
    await task_queue.add_task(task)

    # 创建初始结果
    results = []
    for account in accounts:
        results.append(
            PostResult(
                account_id=account.id,
                username=account.username,
                platform=account.platform,
                success=False,  # 初始状态为未成功
                post_id=None,
                error=None,
            )
        )

    return BatchPostResponse(results=results, task_id=task_id)


@router.get("/platforms")
async def get_supported_platforms():
    """获取支持的社交媒体平台列表"""
    return {
        "platforms": [
            {"id": "douyin", "name": "抖音", "icon": "douyin-icon.png"},
            {"id": "kuaishou", "name": "快手", "icon": "kuaishou-icon.png"},
            {"id": "bilibili", "name": "哔哩哔哩", "icon": "bilibili-icon.png"},
            {"id": "weibo", "name": "微博", "icon": "weibo-icon.png"},
            {"id": "xiaohongshu", "name": "小红书", "icon": "xiaohongshu-icon.png"},
        ]
    }


# 内容分发相关路由
@router.post("/distribute", response_model=DistributionTaskResponse)
async def create_distribution_task(
    task_data: DistributionTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新的内容分发任务"""
    # 检查媒体文件是否存在
    if not os.path.exists(task_data.media_path):
        raise HTTPException(status_code=400, detail="媒体文件不存在")

    # 获取指定的账号
    accounts = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.id.in_(task_data.account_ids),
            SocialAccount.user_id == current_user.id,
        )
        .all()
    )

    if not accounts:
        raise HTTPException(status_code=400, detail="未找到有效账号")

    # 创建分发任务记录
    task_id = str(uuid.uuid4())
    distribution_task = DistributionTask(
        task_id=task_id,
        title=task_data.title,
        description=task_data.description,
        media_path=task_data.media_path,
        platforms=task_data.platforms,
        accounts=[
            {
                "id": account.id,
                "username": account.username,
                "platform": account.platform,
            }
            for account in accounts
        ],
        status="pending",
        progress=0,
        scheduled_time=task_data.scheduled_time,
        user_id=current_user.id,
    )

    db.add(distribution_task)
    db.commit()
    db.refresh(distribution_task)

    # 创建任务队列任务
    task = Task(
        task_id=task_id,
        task_type="content_distribution",
        data={
            "distribution_task_id": distribution_task.id,
            "accounts": [
                {
                    "id": account.id,
                    "username": account.username,
                    "platform": account.platform,
                }
                for account in accounts
            ],
            "media_info": {
                "path": task_data.media_path,
                "title": task_data.title,
                "description": task_data.description,
            },
            "platforms": task_data.platforms,
            "user_id": current_user.id,
            "scheduled_time": (
                task_data.scheduled_time.isoformat()
                if task_data.scheduled_time
                else None
            ),
        },
    )

    # 添加任务到队列
    await task_queue.add_task(task)

    return distribution_task


@router.get("/distribute", response_model=List[DistributionTaskResponse])
async def get_distribution_tasks(
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取内容分发任务列表"""
    query = db.query(DistributionTask).filter(
        DistributionTask.user_id == current_user.id
    )

    if status:
        query = query.filter(DistributionTask.status == status)

    total = query.count()
    tasks = (
        query.order_by(DistributionTask.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return tasks


@router.get("/distribute/{task_id}", response_model=DistributionTaskResponse)
async def get_distribution_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取特定内容分发任务的详情"""
    task = (
        db.query(DistributionTask)
        .filter(
            DistributionTask.task_id == task_id,
            DistributionTask.user_id == current_user.id,
        )
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task
