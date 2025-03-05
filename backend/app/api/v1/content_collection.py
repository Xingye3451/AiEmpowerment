from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Body,
    Path,
    BackgroundTasks,
    UploadFile,
    File,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime
import os
import shutil
import json
import uuid

from app.api import deps
from app.models.user import User
from app.models.content_collection import CollectedVideo, CollectionTask, ContentTag
from app.schemas.content_collection import (
    CollectedVideoCreate,
    CollectedVideoUpdate,
    CollectedVideoResponse,
    CollectionTaskCreate,
    CollectionTaskUpdate,
    CollectionTaskResponse,
    ContentTagCreate,
    ContentTagResponse,
    VideoSearchRequest,
    VideoDownloadRequest,
)
from app.core.config import settings
from app.utils.douyin_crawler import DouyinCrawler
from app.utils.kuaishou_crawler import KuaishouCrawler
from app.utils.bilibili_crawler import BiliBiliCrawler

router = APIRouter()


# 内容搜索相关API
@router.post("/search", response_model=List[CollectedVideoResponse])
async def search_videos(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    search_request: VideoSearchRequest,
):
    """
    搜索视频内容
    """
    # 创建采集任务
    collection_task = CollectionTask(
        name=f"搜索: {search_request.query}",
        query=search_request.query,
        platforms=[search_request.platform],
        filters={
            "time_range": search_request.time_range,
            "sort_by": search_request.sort_by,
            "min_likes": search_request.min_likes,
            "min_views": search_request.min_views,
            "tags": search_request.tags,
        },
        user_id=current_user.id,
        status="running",
    )

    db.add(collection_task)
    db.commit()
    db.refresh(collection_task)

    try:
        # 根据平台选择爬虫
        videos = []
        if search_request.platform == "douyin":
            crawler = DouyinCrawler()
            videos = await crawler.search_videos(
                search_request.query,
                time_range=search_request.time_range,
                sort_by=search_request.sort_by,
                min_likes=search_request.min_likes,
                min_views=search_request.min_views,
                tags=search_request.tags,
                page=search_request.page,
                per_page=search_request.per_page,
            )
        elif search_request.platform == "kuaishou":
            crawler = KuaishouCrawler()
            videos = await crawler.search_videos(
                search_request.query,
                time_range=search_request.time_range,
                sort_by=search_request.sort_by,
                min_likes=search_request.min_likes,
                min_views=search_request.min_views,
                tags=search_request.tags,
                page=search_request.page,
                per_page=search_request.per_page,
            )
        elif search_request.platform == "bilibili":
            crawler = BiliBiliCrawler()
            videos = await crawler.search_videos(
                search_request.query,
                time_range=search_request.time_range,
                sort_by=search_request.sort_by,
                min_likes=search_request.min_likes,
                min_views=search_request.min_views,
                tags=search_request.tags,
                page=search_request.page,
                per_page=search_request.per_page,
            )

        # 保存搜索结果
        db_videos = []
        for video_data in videos:
            # 检查是否已存在
            existing_video = (
                db.query(CollectedVideo)
                .filter(
                    CollectedVideo.platform == search_request.platform,
                    CollectedVideo.platform_video_id == video_data["platform_video_id"],
                )
                .first()
            )

            if existing_video:
                # 更新现有记录
                for key, value in video_data.items():
                    if key != "id" and hasattr(existing_video, key):
                        setattr(existing_video, key, value)

                existing_video.collection_id = collection_task.id
                db.add(existing_video)
                db_videos.append(existing_video)
            else:
                # 创建新记录
                db_video = CollectedVideo(
                    platform=search_request.platform,
                    platform_video_id=video_data["platform_video_id"],
                    title=video_data["title"],
                    description=video_data.get("description", ""),
                    author=video_data["author"],
                    author_id=video_data.get("author_id"),
                    thumbnail=video_data.get("thumbnail"),
                    video_url=video_data.get("video_url"),
                    duration=video_data.get("duration"),
                    stats=video_data.get("stats", {}),
                    tags=video_data.get("tags", []),
                    published_at=video_data.get("published_at"),
                    collection_id=collection_task.id,
                    user_id=current_user.id,
                )
                db.add(db_video)
                db_videos.append(db_video)

            # 更新标签
            if video_data.get("tags"):
                for tag_name in video_data["tags"]:
                    tag = (
                        db.query(ContentTag).filter(ContentTag.name == tag_name).first()
                    )
                    if tag:
                        tag.count += 1
                    else:
                        tag = ContentTag(name=tag_name, count=1)
                    db.add(tag)

        # 更新采集任务状态
        collection_task.status = "completed"
        collection_task.total_found = len(videos)
        collection_task.completed_at = datetime.now()
        db.add(collection_task)

        db.commit()

        # 刷新所有视频对象
        for video in db_videos:
            db.refresh(video)

        return db_videos

    except Exception as e:
        # 更新采集任务状态为失败
        collection_task.status = "failed"
        db.add(collection_task)
        db.commit()

        raise HTTPException(status_code=500, detail=f"搜索视频失败: {str(e)}")


@router.post("/download", response_model=CollectedVideoResponse)
async def download_video(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    background_tasks: BackgroundTasks,
    download_request: VideoDownloadRequest,
):
    """
    下载视频
    """
    video = (
        db.query(CollectedVideo)
        .filter(
            CollectedVideo.id == download_request.video_id,
            CollectedVideo.user_id == current_user.id,
        )
        .first()
    )

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 添加后台任务下载视频
    background_tasks.add_task(
        download_video_task, db=db, video=video, platform=download_request.platform
    )

    return video


async def download_video_task(db: Session, video: CollectedVideo, platform: str):
    """后台下载视频任务"""
    try:
        # 创建下载目录
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "downloads", str(video.user_id)
        )
        os.makedirs(download_dir, exist_ok=True)

        # 生成文件名
        file_name = f"{platform}_{video.platform_video_id}_{uuid.uuid4().hex}.mp4"
        local_path = os.path.join(download_dir, file_name)

        # 根据平台选择下载器
        if platform == "douyin":
            crawler = DouyinCrawler()
            success = await crawler.download_video(video.video_url, local_path)
        elif platform == "kuaishou":
            crawler = KuaishouCrawler()
            success = await crawler.download_video(video.video_url, local_path)
        elif platform == "bilibili":
            crawler = BiliBiliCrawler()
            success = await crawler.download_video(video.video_url, local_path)
        else:
            success = False

        if success:
            # 更新视频记录
            video.local_path = local_path
            video.is_downloaded = True
            db.add(video)
            db.commit()

    except Exception as e:
        print(f"下载视频失败: {str(e)}")


@router.get("/videos", response_model=List[CollectedVideoResponse])
def get_collected_videos(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
    platform: Optional[str] = Query(None, description="平台筛选"),
    is_downloaded: Optional[bool] = Query(None, description="是否已下载"),
    is_favorite: Optional[bool] = Query(None, description="是否收藏"),
    search: Optional[str] = Query(None, description="搜索关键词"),
):
    """
    获取已采集的视频列表
    """
    query = db.query(CollectedVideo).filter(CollectedVideo.user_id == current_user.id)

    if platform:
        query = query.filter(CollectedVideo.platform == platform)

    if is_downloaded is not None:
        query = query.filter(CollectedVideo.is_downloaded == is_downloaded)

    if is_favorite is not None:
        query = query.filter(CollectedVideo.is_favorite == is_favorite)

    if search:
        query = query.filter(
            or_(
                CollectedVideo.title.ilike(f"%{search}%"),
                CollectedVideo.description.ilike(f"%{search}%"),
                CollectedVideo.author.ilike(f"%{search}%"),
            )
        )

    videos = (
        query.order_by(CollectedVideo.created_at.desc()).offset(skip).limit(limit).all()
    )
    return videos


@router.get("/videos/{video_id}", response_model=CollectedVideoResponse)
def get_collected_video(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    video_id: str = Path(..., description="视频ID"),
):
    """
    获取指定视频详情
    """
    video = (
        db.query(CollectedVideo)
        .filter(
            CollectedVideo.id == video_id, CollectedVideo.user_id == current_user.id
        )
        .first()
    )

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    return video


@router.put("/videos/{video_id}", response_model=CollectedVideoResponse)
def update_collected_video(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    video_id: str = Path(..., description="视频ID"),
    video_in: CollectedVideoUpdate,
):
    """
    更新视频信息
    """
    video = (
        db.query(CollectedVideo)
        .filter(
            CollectedVideo.id == video_id, CollectedVideo.user_id == current_user.id
        )
        .first()
    )

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    update_data = video_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(video, field, value)

    db.add(video)
    db.commit()
    db.refresh(video)

    return video


@router.delete("/videos/{video_id}")
def delete_collected_video(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    video_id: str = Path(..., description="视频ID"),
):
    """
    删除视频
    """
    video = (
        db.query(CollectedVideo)
        .filter(
            CollectedVideo.id == video_id, CollectedVideo.user_id == current_user.id
        )
        .first()
    )

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 如果有本地文件，删除文件
    if video.local_path and os.path.exists(video.local_path):
        try:
            os.remove(video.local_path)
        except Exception as e:
            print(f"删除文件失败: {str(e)}")

    db.delete(video)
    db.commit()

    return {"message": "视频已删除"}


@router.get("/videos/{video_id}/file")
def get_video_file(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    video_id: str = Path(..., description="视频ID"),
):
    """
    获取视频文件
    """
    video = (
        db.query(CollectedVideo)
        .filter(
            CollectedVideo.id == video_id, CollectedVideo.user_id == current_user.id
        )
        .first()
    )

    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if (
        not video.is_downloaded
        or not video.local_path
        or not os.path.exists(video.local_path)
    ):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    return FileResponse(
        path=video.local_path, filename=f"{video.title}.mp4", media_type="video/mp4"
    )


# 采集任务相关API
@router.post("/tasks", response_model=CollectionTaskResponse)
def create_collection_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_in: CollectionTaskCreate,
):
    """
    创建采集任务
    """
    db_task = CollectionTask(
        name=task_in.name,
        query=task_in.query,
        platforms=task_in.platforms,
        filters=task_in.filters,
        user_id=current_user.id,
        scheduled_task_id=task_in.scheduled_task_id,
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@router.get("/tasks", response_model=List[CollectionTaskResponse])
def get_collection_tasks(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取采集任务列表
    """
    tasks = (
        db.query(CollectionTask)
        .filter(CollectionTask.user_id == current_user.id)
        .order_by(CollectionTask.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return tasks


@router.get("/tasks/{task_id}", response_model=CollectionTaskResponse)
def get_collection_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: str = Path(..., description="任务ID"),
):
    """
    获取指定采集任务详情
    """
    task = (
        db.query(CollectionTask)
        .filter(CollectionTask.id == task_id, CollectionTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取关联的视频
    videos = (
        db.query(CollectedVideo).filter(CollectedVideo.collection_id == task.id).all()
    )

    response = task.__dict__.copy()
    response["videos"] = videos

    return response


@router.put("/tasks/{task_id}", response_model=CollectionTaskResponse)
def update_collection_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: str = Path(..., description="任务ID"),
    task_in: CollectionTaskUpdate,
):
    """
    更新采集任务
    """
    task = (
        db.query(CollectionTask)
        .filter(CollectionTask.id == task_id, CollectionTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = task_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.delete("/tasks/{task_id}")
def delete_collection_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    task_id: str = Path(..., description="任务ID"),
):
    """
    删除采集任务
    """
    task = (
        db.query(CollectionTask)
        .filter(CollectionTask.id == task_id, CollectionTask.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 删除关联的视频
    videos = (
        db.query(CollectedVideo).filter(CollectedVideo.collection_id == task.id).all()
    )

    for video in videos:
        # 如果有本地文件，删除文件
        if video.local_path and os.path.exists(video.local_path):
            try:
                os.remove(video.local_path)
            except Exception as e:
                print(f"删除文件失败: {str(e)}")

        db.delete(video)

    db.delete(task)
    db.commit()

    return {"message": "任务已删除"}


# 标签相关API
@router.get("/tags", response_model=List[ContentTagResponse])
def get_content_tags(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取内容标签列表
    """
    tags = (
        db.query(ContentTag)
        .order_by(ContentTag.count.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return tags


@router.post("/tags", response_model=ContentTagResponse)
def create_content_tag(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    tag_in: ContentTagCreate,
):
    """
    创建内容标签
    """
    # 检查是否已存在
    existing_tag = db.query(ContentTag).filter(ContentTag.name == tag_in.name).first()
    if existing_tag:
        raise HTTPException(status_code=400, detail="标签已存在")

    db_tag = ContentTag(name=tag_in.name, category=tag_in.category, count=0)

    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)

    return db_tag
