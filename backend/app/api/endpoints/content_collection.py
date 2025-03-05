from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.content_collection import CollectionTask, CollectedContent
from app.schemas.content_collection import (
    CollectionTaskCreate,
    CollectionTaskUpdate,
    CollectionTaskResponse,
    CollectedContentResponse,
    CollectionTaskListResponse,
    CollectionTaskDetailResponse,
)
from app.utils.douyin_crawler import DouyinCrawler
from app.utils.kuaishou_crawler import KuaishouCrawler
from app.utils.bilibili_crawler import BiliBiliCrawler
import asyncio
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/tasks", response_model=CollectionTaskResponse)
async def create_collection_task(
    task_data: CollectionTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """创建内容采集任务"""
    # 创建任务记录
    task = CollectionTask(
        name=task_data.name,
        query=task_data.query,
        platforms=task_data.platforms,
        filters=task_data.filters,
        status="pending",
        user_id=current_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # 添加后台任务
    background_tasks.add_task(run_collection_task, task.id, db)

    return task


@router.get("/tasks", response_model=CollectionTaskListResponse)
async def list_collection_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取用户的内容采集任务列表"""
    query = db.query(CollectionTask).filter(CollectionTask.user_id == current_user.id)

    if status:
        query = query.filter(CollectionTask.status == status)

    total = query.count()
    tasks = (
        query.order_by(CollectionTask.created_at.desc()).offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "items": tasks,
    }


@router.get("/tasks/{task_id}", response_model=CollectionTaskDetailResponse)
async def get_collection_task(
    task_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取采集任务详情"""
    task = (
        db.query(CollectionTask)
        .filter(CollectionTask.id == task_id, CollectionTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取采集到的内容
    contents = (
        db.query(CollectedContent)
        .filter(CollectedContent.collection_task_id == task_id)
        .all()
    )

    return {
        "task": task,
        "contents": contents,
    }


@router.put("/tasks/{task_id}", response_model=CollectionTaskResponse)
async def update_collection_task(
    task_id: str,
    task_data: CollectionTaskUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """更新采集任务"""
    task = (
        db.query(CollectionTask)
        .filter(CollectionTask.id == task_id, CollectionTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 只有pending状态的任务可以更新
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="只有待处理的任务可以更新")

    # 更新任务信息
    for key, value in task_data.dict(exclude_unset=True).items():
        setattr(task, key, value)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.delete("/tasks/{task_id}")
async def delete_collection_task(
    task_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """删除采集任务"""
    task = (
        db.query(CollectionTask)
        .filter(CollectionTask.id == task_id, CollectionTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 删除关联的内容
    db.query(CollectedContent).filter(
        CollectedContent.collection_task_id == task_id
    ).delete()

    # 删除任务
    db.delete(task)
    db.commit()

    return {"message": "任务已删除"}


@router.get("/contents", response_model=List[CollectedContentResponse])
async def list_collected_contents(
    skip: int = 0,
    limit: int = 100,
    task_id: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取采集到的内容列表"""
    query = db.query(CollectedContent).filter(
        CollectedContent.user_id == current_user.id
    )

    if task_id:
        query = query.filter(CollectedContent.collection_task_id == task_id)

    if platform:
        query = query.filter(CollectedContent.platform == platform)

    if status:
        query = query.filter(CollectedContent.status == status)

    contents = (
        query.order_by(CollectedContent.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return contents


@router.get("/contents/{content_id}", response_model=CollectedContentResponse)
async def get_collected_content(
    content_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取采集到的内容详情"""
    content = (
        db.query(CollectedContent)
        .filter(
            CollectedContent.id == content_id,
            CollectedContent.user_id == current_user.id,
        )
        .first()
    )

    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    return content


@router.delete("/contents/{content_id}")
async def delete_collected_content(
    content_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """删除采集到的内容"""
    content = (
        db.query(CollectedContent)
        .filter(
            CollectedContent.id == content_id,
            CollectedContent.user_id == current_user.id,
        )
        .first()
    )

    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    db.delete(content)
    db.commit()

    return {"message": "内容已删除"}


@router.post("/tasks/{task_id}/run")
async def run_task_manually(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """手动运行采集任务"""
    task = (
        db.query(CollectionTask)
        .filter(CollectionTask.id == task_id, CollectionTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 只有非运行中的任务可以手动运行
    if task.status == "running":
        raise HTTPException(status_code=400, detail="任务已在运行中")

    # 更新任务状态
    task.status = "pending"
    db.add(task)
    db.commit()

    # 添加后台任务
    background_tasks.add_task(run_collection_task, task.id, db)

    return {"message": "任务已开始运行"}


async def run_collection_task(task_id: str, db: Session):
    """运行采集任务"""
    try:
        # 获取任务信息
        task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return

        # 更新任务状态
        task.status = "running"
        task.started_at = datetime.now()
        db.add(task)
        db.commit()

        # 获取任务数据
        query = task.query
        platforms = task.platforms
        filters = task.filters or {}

        total_found = 0

        # 对每个平台执行搜索
        for platform in platforms:
            try:
                # 选择爬虫
                crawler = None
                if platform == "douyin":
                    crawler = DouyinCrawler()
                elif platform == "kuaishou":
                    crawler = KuaishouCrawler()
                elif platform == "bilibili":
                    crawler = BiliBiliCrawler()

                if not crawler:
                    logger.warning(f"不支持的平台: {platform}")
                    continue

                # 执行搜索
                videos = await crawler.search_videos(
                    query,
                    time_range=filters.get("time_range", "today"),
                    sort_by=filters.get("sort_by", "likes"),
                    min_likes=filters.get("min_likes"),
                    min_views=filters.get("min_views"),
                    tags=filters.get("tags"),
                    page=1,
                    per_page=20,
                )

                # 保存视频数据
                for video in videos:
                    # 检查是否已存在
                    existing = (
                        db.query(CollectedContent)
                        .filter(
                            CollectedContent.platform == platform,
                            CollectedContent.content_id == video["id"],
                        )
                        .first()
                    )

                    if existing:
                        continue

                    # 创建新内容记录
                    content = CollectedContent(
                        platform=platform,
                        content_id=video["id"],
                        title=video.get("title"),
                        description=video.get("description"),
                        author=video.get("author"),
                        author_id=video.get("author_id"),
                        url=video.get("url"),
                        thumbnail_url=video.get("thumbnail"),
                        video_url=video.get("video_url"),
                        duration=video.get("duration"),
                        likes=video.get("likes", 0),
                        comments=video.get("comments", 0),
                        shares=video.get("shares", 0),
                        views=video.get("views", 0),
                        published_at=video.get("published_at"),
                        metadata=video.get("metadata"),
                        status="collected",
                        collection_task_id=task.id,
                        user_id=task.user_id,
                    )

                    db.add(content)
                    total_found += 1

                db.commit()

            except Exception as e:
                logger.error(f"平台 {platform} 搜索失败: {str(e)}")

        # 更新任务状态
        task.status = "completed"
        task.total_found = total_found
        task.completed_at = datetime.now()
        db.add(task)
        db.commit()

    except Exception as e:
        logger.error(f"执行采集任务 {task_id} 失败: {str(e)}")
        # 更新任务状态为失败
        try:
            task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
            if task:
                task.status = "failed"
                db.add(task)
                db.commit()
        except Exception as inner_e:
            logger.error(f"更新任务状态失败: {str(inner_e)}")
