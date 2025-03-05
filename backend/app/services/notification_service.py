from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationService:
    """通知服务"""

    @staticmethod
    def create_notification(
        db: Session, notification_data: NotificationCreate
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
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def create_system_notification(
        db: Session, user_id: str, title: str, content: str
    ) -> Notification:
        """创建系统通知"""
        notification_data = NotificationCreate(
            title=title, content=content, type="system", user_id=user_id
        )

        return NotificationService.create_notification(db, notification_data)

    @staticmethod
    def create_task_notification(
        db: Session,
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

        return NotificationService.create_notification(db, notification_data)

    @staticmethod
    def create_scheduled_task_notification(
        db: Session, user_id: str, title: str, content: str, task_id: str
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

        return NotificationService.create_notification(db, notification_data)

    @staticmethod
    def get_notifications(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        type: Optional[str] = None,
    ) -> List[Notification]:
        """获取用户通知列表"""
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if status:
            query = query.filter(Notification.status == status)

        if type:
            query = query.filter(Notification.type == type)

        return (
            query.order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_notification_by_id(
        db: Session, notification_id: str, user_id: str
    ) -> Optional[Notification]:
        """根据ID获取通知"""
        return (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

    @staticmethod
    def update_notification(
        db: Session, notification: Notification, notification_data: NotificationUpdate
    ) -> Notification:
        """更新通知"""
        for key, value in notification_data.dict(exclude_unset=True).items():
            setattr(notification, key, value)

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def mark_as_read(db: Session, notification: Notification) -> Notification:
        """将通知标记为已读"""
        notification_data = NotificationUpdate(status="read", read_at=datetime.now())

        return NotificationService.update_notification(
            db, notification, notification_data
        )

    @staticmethod
    def mark_all_as_read(db: Session, user_id: str) -> int:
        """将用户所有未读通知标记为已读"""
        now = datetime.now()
        result = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.status == "unread")
            .update({"status": "read", "read_at": now})
        )

        db.commit()

        return result

    @staticmethod
    def delete_notification(db: Session, notification: Notification) -> bool:
        """删除通知"""
        db.delete(notification)
        db.commit()

        return True

    @staticmethod
    def get_notification_count(db: Session, user_id: str) -> Dict[str, int]:
        """获取用户通知计数"""
        total = db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.status == "unread")
            .count()
        )

        return {"total": total, "unread": unread}
