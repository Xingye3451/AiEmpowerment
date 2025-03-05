from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from datetime import datetime
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationService:
    """通知服务"""

    @staticmethod
    async def create_notification(
        db: AsyncSession, notification_data: NotificationCreate
    ) -> Notification:
        """创建通知"""
        notification = Notification(
            title=notification_data.title,
            content=notification_data.content,
            type=notification_data.type,
            related_id=notification_data.related_id,
            related_type=notification_data.related_type,
            user_id=notification_data.user_id,
            status="unread",
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        return notification

    @staticmethod
    async def create_system_notification(
        db: AsyncSession, user_id: str, title: str, content: str
    ) -> Notification:
        """创建系统通知"""
        notification_data = NotificationCreate(
            title=title, content=content, type="system", user_id=user_id
        )

        return await NotificationService.create_notification(db, notification_data)

    @staticmethod
    async def create_task_notification(
        db: AsyncSession,
        user_id: str,
        title: str,
        content: str,
        task_id: str,
        task_type: str,
    ) -> Notification:
        """创建任务相关通知"""
        notification_data = NotificationCreate(
            title=title,
            content=content,
            type="task",
            related_id=task_id,
            related_type=task_type,
            user_id=user_id,
        )

        return await NotificationService.create_notification(db, notification_data)

    @staticmethod
    async def create_scheduled_task_notification(
        db: AsyncSession, user_id: str, title: str, content: str, task_id: str
    ) -> Notification:
        """创建定时任务相关通知"""
        notification_data = NotificationCreate(
            title=title,
            content=content,
            type="scheduled_task",
            related_id=task_id,
            related_type="scheduled_task",
            user_id=user_id,
        )

        return await NotificationService.create_notification(db, notification_data)

    @staticmethod
    async def get_notifications(
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        type: Optional[str] = None,
    ) -> List[Notification]:
        """获取用户通知列表"""
        query = select(Notification).where(Notification.user_id == user_id)

        if status:
            query = query.where(Notification.status == status)

        if type:
            query = query.where(Notification.type == type)

        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_notification_by_id(
        db: AsyncSession, notification_id: str, user_id: str
    ) -> Optional[Notification]:
        """根据ID获取通知"""
        query = select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_notification(
        db: AsyncSession,
        notification: Notification,
        notification_data: NotificationUpdate,
    ) -> Notification:
        """更新通知"""
        for key, value in notification_data.dict(exclude_unset=True).items():
            setattr(notification, key, value)

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        return notification

    @staticmethod
    async def mark_as_read(
        db: AsyncSession, notification: Notification
    ) -> Notification:
        """将通知标记为已读"""
        notification_data = NotificationUpdate(status="read", read_at=datetime.now())

        return await NotificationService.update_notification(
            db, notification, notification_data
        )

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: str) -> int:
        """将用户所有未读通知标记为已读"""
        now = datetime.now()

        # 使用异步更新
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.status == "unread")
            .values(status="read", read_at=now)
        )
        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount

    @staticmethod
    async def delete_notification(db: AsyncSession, notification: Notification) -> bool:
        """删除通知"""
        await db.delete(notification)
        await db.commit()
        return True

    @staticmethod
    async def get_notification_count(db: AsyncSession, user_id: str) -> Dict[str, int]:
        """获取用户通知计数"""
        # 获取总数
        total_query = select(func.count()).where(Notification.user_id == user_id)
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        # 获取未读数
        unread_query = select(func.count()).where(
            Notification.user_id == user_id, Notification.status == "unread"
        )
        unread_result = await db.execute(unread_query)
        unread = unread_result.scalar() or 0

        return {"total": total, "unread": unread}
