from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.api import deps
from app.models.user import User
from app.models.scheduled_task import ScheduledTask
from app.schemas.scheduled_task import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskResponse,
)
from app.core.scheduler import scheduler

router = APIRouter()


@router.post("/", response_model=ScheduledTaskResponse)
def create_scheduled_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_in: ScheduledTaskCreate
):
    """
    创建定时任务
    """
    # 创建任务记录
    db_task = ScheduledTask(
        name=task_in.name,
        type=task_in.type,
        schedule=task_in.schedule.dict(),
        data=task_in.data,
        user_id=current_user.id,
    )

    # 计算下次执行时间
    next_run = calculate_next_run(task_in.schedule.dict())
    db_task.next_run = next_run

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 添加到调度器
    add_task_to_scheduler(db_task)

    return db_task


@router.get("/", response_model=List[ScheduledTaskResponse])
def get_scheduled_tasks(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
    task_type: Optional[str] = Query(None, description="任务类型筛选")
):
    """
    获取当前用户的定时任务列表
    """
    query = db.query(ScheduledTask).filter(ScheduledTask.user_id == current_user.id)

    if task_type:
        query = query.filter(ScheduledTask.type == task_type)

    tasks = (
        query.order_by(ScheduledTask.created_at.desc()).offset(skip).limit(limit).all()
    )
    return tasks


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
def get_scheduled_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: str = Path(..., description="任务ID")
):
    """
    获取指定定时任务详情
    """
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.put("/{task_id}", response_model=ScheduledTaskResponse)
def update_scheduled_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: str = Path(..., description="任务ID"),
    task_in: ScheduledTaskUpdate
):
    """
    更新定时任务
    """
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = task_in.dict(exclude_unset=True)

    # 如果更新了计划，重新计算下次执行时间
    if "schedule" in update_data:
        update_data["next_run"] = calculate_next_run(update_data["schedule"])

    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)

    # 更新调度器中的任务
    update_task_in_scheduler(task)

    return task


@router.delete("/{task_id}")
def delete_scheduled_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: str = Path(..., description="任务ID")
):
    """
    删除定时任务
    """
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 从调度器中移除任务
    remove_task_from_scheduler(task)

    db.delete(task)
    db.commit()

    return {"message": "任务已删除"}


@router.patch("/{task_id}/status", response_model=ScheduledTaskResponse)
def update_task_status(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: str = Path(..., description="任务ID"),
    status: str = Body(..., embed=True)
):
    """
    更新任务状态（激活/暂停）
    """
    if status not in ["active", "paused"]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = status
    db.add(task)
    db.commit()
    db.refresh(task)

    # 更新调度器中的任务状态
    if status == "active":
        activate_task_in_scheduler(task)
    else:
        pause_task_in_scheduler(task)

    return task


# 辅助函数
def calculate_next_run(schedule):
    """计算下次执行时间"""
    now = datetime.now()
    schedule_type = schedule["type"]
    time_parts = schedule["time"].split(":")
    hours, minutes, seconds = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])

    if schedule_type == "once":
        # 一次性任务，直接设置时间
        next_run = now.replace(hour=hours, minute=minutes, second=seconds)
        if next_run < now:
            next_run = next_run + timedelta(days=1)

    elif schedule_type == "daily":
        # 每日任务
        next_run = now.replace(hour=hours, minute=minutes, second=seconds)
        if next_run < now:
            next_run = next_run + timedelta(days=1)

    elif schedule_type == "weekly":
        # 每周任务
        days = schedule.get("days", [])
        if not days:
            # 如果没有指定星期几，默认为当前星期
            next_run = now.replace(hour=hours, minute=minutes, second=seconds)
            if next_run < now:
                next_run = next_run + timedelta(days=7)
        else:
            # 计算下一个符合条件的星期几
            day_map = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4,
                "saturday": 5,
                "sunday": 6,
            }
            day_numbers = [day_map[day] for day in days if day in day_map]
            if not day_numbers:
                next_run = now.replace(hour=hours, minute=minutes, second=seconds)
                if next_run < now:
                    next_run = next_run + timedelta(days=1)
            else:
                current_weekday = now.weekday()
                next_weekdays = [d for d in day_numbers if d > current_weekday] or [
                    d + 7 for d in day_numbers
                ]
                days_ahead = min(next_weekdays) - current_weekday
                next_run = now.replace(
                    hour=hours, minute=minutes, second=seconds
                ) + timedelta(days=days_ahead)
                if next_run < now and days_ahead == 0:
                    next_run = next_run + timedelta(days=7)

    elif schedule_type == "monthly":
        # 每月任务
        day = schedule.get("date", 1)
        next_run = now.replace(
            day=min(day, 28), hour=hours, minute=minutes, second=seconds
        )
        if next_run < now:
            # 移到下个月
            if now.month == 12:
                next_run = next_run.replace(year=now.year + 1, month=1)
            else:
                next_run = next_run.replace(month=now.month + 1)

    else:
        # 默认为当前时间
        next_run = now

    return next_run


def add_task_to_scheduler(task):
    """添加任务到调度器"""
    # 这里应该实现实际的调度逻辑
    # 例如使用APScheduler添加任务
    pass


def update_task_in_scheduler(task):
    """更新调度器中的任务"""
    # 先移除旧任务，再添加新任务
    remove_task_from_scheduler(task)
    if task.status == "active":
        add_task_to_scheduler(task)


def remove_task_from_scheduler(task):
    """从调度器中移除任务"""
    # 实现实际的移除逻辑
    pass


def activate_task_in_scheduler(task):
    """激活调度器中的任务"""
    # 实现实际的激活逻辑
    add_task_to_scheduler(task)


def pause_task_in_scheduler(task):
    """暂停调度器中的任务"""
    # 实现实际的暂停逻辑
    remove_task_from_scheduler(task)
