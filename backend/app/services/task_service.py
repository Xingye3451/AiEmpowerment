from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """任务服务类"""

    @staticmethod
    async def create_task(db: AsyncSession, task_data: TaskCreate) -> Task:
        """创建任务"""
        task = Task(
            task_type=task_data.task_type,
            status="pending",
            data=task_data.data,
            user_id=task_data.user_id,
            max_retries=task_data.max_retries,
            scheduled_at=task_data.scheduled_at,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        return task

    @staticmethod
    async def get_task(db: AsyncSession, task_id: str) -> Optional[Task]:
        """获取任务"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalars().first()

    @staticmethod
    async def get_tasks(
        db: AsyncSession,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """获取任务列表"""
        query = select(Task)

        if user_id:
            query = query.where(Task.user_id == user_id)

        if status:
            # 支持多个状态，用逗号分隔
            if "," in status:
                status_list = status.split(",")
                query = query.where(Task.status.in_(status_list))
            else:
                query = query.where(Task.status == status)

        if task_type:
            query = query.where(Task.task_type == task_type)

        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_task(
        db: AsyncSession, task_id: str, task_data: TaskUpdate
    ) -> Optional[Task]:
        """更新任务"""
        task = await TaskService.get_task(db, task_id)
        if not task:
            return None

        update_data = task_data.dict(exclude_unset=True)

        # 更新任务
        for key, value in update_data.items():
            setattr(task, key, value)

        # 更新时间
        task.updated_at = datetime.now()

        await db.commit()
        await db.refresh(task)

        return task

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: str) -> bool:
        """删除任务"""
        task = await TaskService.get_task(db, task_id)
        if not task:
            return False

        await db.delete(task)
        await db.commit()

        return True

    @staticmethod
    async def count_tasks(
        db: AsyncSession,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> int:
        """统计任务数量"""
        query = select(Task)

        if user_id:
            query = query.where(Task.user_id == user_id)

        if status:
            # 支持多个状态，用逗号分隔
            if "," in status:
                status_list = status.split(",")
                query = query.where(Task.status.in_(status_list))
            else:
                query = query.where(Task.status == status)

        if task_type:
            query = query.where(Task.task_type == task_type)

        result = await db.execute(query)
        return len(result.scalars().all())
