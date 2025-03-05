from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.scheduled_task import ScheduledTask
from app.schemas.scheduled_task import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskResponse,
    ScheduledTaskListResponse,
)
from app.core.scheduler import scheduler
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ScheduledTaskResponse)
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """创建定时任务"""
    # 创建任务记录
    task = ScheduledTask(
        name=task_data.name,
        description=task_data.description,
        type=task_data.type,
        status="active",
        schedule=task_data.schedule,
        data=task_data.data,
        user_id=current_user.id,
        next_run=calculate_next_run(task_data.schedule),
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # 添加到调度器
    scheduler.add_task(task)

    return task


@router.get("/", response_model=ScheduledTaskListResponse)
async def list_scheduled_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取用户的定时任务列表"""
    query = db.query(ScheduledTask).filter(ScheduledTask.user_id == current_user.id)

    if status:
        query = query.filter(ScheduledTask.status == status)

    if type:
        query = query.filter(ScheduledTask.type == type)

    total = query.count()
    tasks = (
        query.order_by(ScheduledTask.created_at.desc()).offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "items": tasks,
    }


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取定时任务详情"""
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.put("/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: str,
    task_data: ScheduledTaskUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """更新定时任务"""
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 更新任务信息
    update_data = task_data.dict(exclude_unset=True)

    # 如果更新了调度信息，重新计算下次执行时间
    if "schedule" in update_data:
        update_data["next_run"] = calculate_next_run(update_data["schedule"])

    for key, value in update_data.items():
        setattr(task, key, value)

    db.add(task)
    db.commit()
    db.refresh(task)

    # 更新调度器中的任务
    scheduler.update_task(task)

    return task


@router.delete("/{task_id}")
async def delete_scheduled_task(
    task_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """删除定时任务"""
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 从调度器中移除任务
    scheduler.remove_task(task.id)

    # 删除任务
    db.delete(task)
    db.commit()

    return {"message": "任务已删除"}


@router.post("/{task_id}/pause")
async def pause_scheduled_task(
    task_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """暂停定时任务"""
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 更新任务状态
    task.status = "paused"
    db.add(task)
    db.commit()
    db.refresh(task)

    # 更新调度器中的任务
    scheduler.update_task(task)

    return {"message": "任务已暂停"}


@router.post("/{task_id}/resume")
async def resume_scheduled_task(
    task_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """恢复定时任务"""
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 更新任务状态
    task.status = "active"
    task.next_run = calculate_next_run(task.schedule)
    db.add(task)
    db.commit()
    db.refresh(task)

    # 更新调度器中的任务
    scheduler.update_task(task)

    return {"message": "任务已恢复"}


@router.post("/{task_id}/run_now")
async def run_scheduled_task_now(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """立即执行定时任务"""
    task = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 添加后台任务执行
    background_tasks.add_task(run_task_immediately, task.id, db)

    return {"message": "任务已开始执行"}


async def run_task_immediately(task_id: str, db: Session):
    """立即执行任务"""
    try:
        # 获取任务信息
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return

        # 执行任务
        scheduler._execute_task(
            task.id,
            {
                "id": task.id,
                "name": task.name,
                "type": task.type,
                "status": task.status,
                "schedule": task.schedule,
                "data": task.data,
                "next_run": datetime.now(),
                "user_id": task.user_id,
            },
        )

    except Exception as e:
        logger.error(f"执行任务 {task_id} 失败: {str(e)}")


def calculate_next_run(schedule: Dict[str, Any]) -> datetime:
    """计算下次执行时间"""
    now = datetime.now()
    schedule_type = schedule.get("type", "once")
    time_parts = schedule.get("time", "00:00:00").split(":")
    hours, minutes, seconds = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])

    if schedule_type == "once":
        # 一次性任务，直接设置时间
        next_run = now.replace(hour=hours, minute=minutes, second=seconds)
        if next_run < now:
            next_run = next_run.replace(day=now.day + 1)

    elif schedule_type == "daily":
        # 每日任务
        next_run = now.replace(hour=hours, minute=minutes, second=seconds)
        if next_run < now:
            next_run = next_run.replace(day=now.day + 1)

    elif schedule_type == "weekly":
        # 每周任务
        days = schedule.get("days", [])
        if not days:
            # 如果没有指定星期几，默认为当前星期
            next_run = now.replace(hour=hours, minute=minutes, second=seconds)
            if next_run < now:
                next_run = next_run.replace(day=now.day + 7)
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
                    next_run = next_run.replace(day=now.day + 1)
            else:
                current_weekday = now.weekday()
                next_weekdays = [d for d in day_numbers if d > current_weekday] or [
                    d + 7 for d in day_numbers
                ]
                days_ahead = min(next_weekdays) - current_weekday
                next_run = now.replace(hour=hours, minute=minutes, second=seconds)
                next_run = next_run.replace(day=now.day + days_ahead)
                if next_run < now and days_ahead == 0:
                    next_run = next_run.replace(day=now.day + 7)

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
