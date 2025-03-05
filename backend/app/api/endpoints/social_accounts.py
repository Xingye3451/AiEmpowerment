from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.social_account import SocialAccount, AccountGroup
from app.schemas.social_account import (
    SocialAccountCreate,
    SocialAccountUpdate,
    SocialAccountResponse,
    AccountGroupCreate,
    AccountGroupResponse,
    AccountGroupUpdate,
)

router = APIRouter()


@router.get("/accounts", response_model=List[SocialAccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取当前用户的所有社交账号
    """
    result = await db.execute(
        select(SocialAccount)
        .filter(SocialAccount.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    accounts = result.scalars().all()
    return accounts


@router.post("/accounts", response_model=SocialAccountResponse)
async def create_account(
    account_in: SocialAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建新的社交账号
    """
    account = SocialAccount(
        username=account_in.username,
        password=account_in.password,
        platform=account_in.platform,
        status="inactive",
        user_id=current_user.id,
        cookies=account_in.cookies,
        extra_data=account_in.extra_data,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/accounts/{account_id}", response_model=SocialAccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取特定社交账号的详细信息
    """
    result = await db.execute(
        select(SocialAccount).filter(
            SocialAccount.id == account_id, SocialAccount.user_id == current_user.id
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在或无权访问")
    return account


@router.put("/accounts/{account_id}", response_model=SocialAccountResponse)
async def update_account(
    account_id: int,
    account_in: SocialAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新社交账号信息
    """
    result = await db.execute(
        select(SocialAccount).filter(
            SocialAccount.id == account_id, SocialAccount.user_id == current_user.id
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在或无权访问")

    update_data = account_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    account.updated_at = datetime.now()
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/accounts/{account_id}", response_model=SocialAccountResponse)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除社交账号
    """
    result = await db.execute(
        select(SocialAccount).filter(
            SocialAccount.id == account_id, SocialAccount.user_id == current_user.id
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在或无权访问")

    await db.delete(account)
    await db.commit()
    return account


@router.get("/groups", response_model=List[AccountGroupResponse])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取当前用户的所有账号组
    """
    result = await db.execute(
        select(AccountGroup)
        .filter(AccountGroup.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    groups = result.scalars().all()
    return groups


@router.post("/groups", response_model=AccountGroupResponse)
async def create_group(
    group_in: AccountGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建新的账号组
    """
    group = AccountGroup(
        name=group_in.name,
        description=group_in.description,
        user_id=current_user.id,
    )

    # 添加账号到组
    if group_in.account_ids:
        for account_id in group_in.account_ids:
            result = await db.execute(
                select(SocialAccount).filter(
                    SocialAccount.id == account_id,
                    SocialAccount.user_id == current_user.id,
                )
            )
            account = result.scalars().first()
            if account:
                group.accounts.append(account)

    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.get("/groups/{group_id}", response_model=AccountGroupResponse)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取特定账号组的详细信息
    """
    result = await db.execute(
        select(AccountGroup).filter(
            AccountGroup.id == group_id, AccountGroup.user_id == current_user.id
        )
    )
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="账号组不存在或无权访问")
    return group


@router.put("/groups/{group_id}", response_model=AccountGroupResponse)
async def update_group(
    group_id: int,
    group_in: AccountGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新账号组信息
    """
    result = await db.execute(
        select(AccountGroup).filter(
            AccountGroup.id == group_id, AccountGroup.user_id == current_user.id
        )
    )
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="账号组不存在或无权访问")

    # 更新基本信息
    if group_in.name is not None:
        group.name = group_in.name
    if group_in.description is not None:
        group.description = group_in.description

    # 更新账号关联
    if group_in.account_ids is not None:
        # 清除现有关联
        group.accounts = []

        # 添加新关联
        for account_id in group_in.account_ids:
            result = await db.execute(
                select(SocialAccount).filter(
                    SocialAccount.id == account_id,
                    SocialAccount.user_id == current_user.id,
                )
            )
            account = result.scalars().first()
            if account:
                group.accounts.append(account)

    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/groups/{group_id}", response_model=AccountGroupResponse)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除账号组
    """
    result = await db.execute(
        select(AccountGroup).filter(
            AccountGroup.id == group_id, AccountGroup.user_id == current_user.id
        )
    )
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="账号组不存在或无权访问")

    await db.delete(group)
    await db.commit()
    return group
