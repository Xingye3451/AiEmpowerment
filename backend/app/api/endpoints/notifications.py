from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取用户通知列表"""
    notifications = NotificationService.get_notifications(
        db=db, user_id=current_user.id, skip=skip, limit=limit, status=status, type=type
    )

    # 获取未读通知数量
    unread_count = NotificationService.get_notification_count(db, current_user.id)[
        "unread"
    ]

    return {
        "total": len(notifications),
        "unread_count": unread_count,
        "items": notifications,
    }


@router.get("/count", response_model=NotificationCountResponse)
async def get_notification_count(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取用户通知计数"""
    counts = NotificationService.get_notification_count(db, current_user.id)

    return counts


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取通知详情"""
    notification = NotificationService.get_notification_by_id(
        db, notification_id, current_user.id
    )

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    return notification


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """将通知标记为已读"""
    notification = NotificationService.get_notification_by_id(
        db, notification_id, current_user.id
    )

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    NotificationService.mark_as_read(db, notification)

    return {"message": "通知已标记为已读"}


@router.post("/read-all")
async def mark_all_as_read(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """将所有通知标记为已读"""
    count = NotificationService.mark_all_as_read(db, current_user.id)

    return {"message": f"已将 {count} 条通知标记为已读"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """删除通知"""
    notification = NotificationService.get_notification_by_id(
        db, notification_id, current_user.id
    )

    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")

    NotificationService.delete_notification(db, notification)

    return {"message": "通知已删除"}
