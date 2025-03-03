from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os
from datetime import datetime
import uuid
import mimetypes
from pathlib import Path
import subprocess
import asyncio

from app.core.deps import get_db, get_current_user
from app.schemas.user import (
    BatchDouyinLogin, BatchDouyinLoginResponse,
    BatchDouyinPost, BatchDouyinPostResponse,
    DouyinLoginResponse, DouyinPostResponse,
    DouyinGroup, ScheduledPost, DouyinStats
)
from app.models.user import User
from app.core.task_queue import TaskQueue, Task, TaskStatus

router = APIRouter()

# 配置目录
UPLOAD_DIR = "uploads/videos"
PREVIEW_DIR = "static/previews"
PROCESSED_DIR = "uploads/processed_videos"

# 创建必要的目录
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# 获取任务队列单例
task_queue = TaskQueue()

@router.post("/batch-login", response_model=BatchDouyinLoginResponse)
async def batch_login_douyin(
    login_data: BatchDouyinLogin,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []
    douyin_accounts = current_user.douyin_accounts or {}
    
    for account in login_data.accounts:
        try:
            # 这里需要集成实际的抖音登录API
            # 此处为示例代码
            success = True  # 实际需要根据登录结果设置
            if success:
                douyin_accounts[account.username] = {
                    "password": account.password,
                    "logged_in": True
                }
            
            results.append(
                DouyinLoginResponse(
                    username=account.username,
                    success=success,
                    error=None if success else "登录失败"
                )
            )
        except Exception as e:
            results.append(
                DouyinLoginResponse(
                    username=account.username,
                    success=False,
                    error=str(e)
                )
            )
    
    # 更新用户的抖音账号信息
    current_user.douyin_accounts = douyin_accounts
    db.commit()
    
    return BatchDouyinLoginResponse(results=results)

@router.post("/upload-video")
async def upload_video(
    video: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{video.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 保存上传的视频文件
        with open(file_path, "wb+") as file_object:
            # 读取文件内容并写入
            content = await video.read()
            file_object.write(content)
            
        return {
            "success": True,
            "file_path": file_path,
            "title": title,
            "description": description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 更新原有的batch_post路由以支持发布历史记录
@router.post("/batch-post")
async def batch_post_video(
    accounts: List[str] = Form(...),
    video_path: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail="视频文件不存在")
    
    task_id = str(uuid.uuid4())
    task = Task(
        task_id=task_id,
        task_type="douyin_post",
        data={
            "accounts": accounts,
            "video_info": {
                "path": video_path,
                "title": title,
                "description": description
            },
            "user_id": current_user.id
        }
    )
    
    # 创建历史记录
    history = current_user.douyin_history or []
    history.append({
        "task_id": task_id,
        "video_id": str(uuid.uuid4()),  # 临时视频ID
        "title": title,
        "description": description,
        "accounts": accounts,
        "success_count": 0,
        "failed_count": 0,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "retries": 0
    })
    current_user.douyin_history = history
    db.commit()
    
    await task_queue.add_task(task)
    
    return {
        "task_id": task_id,
        "message": "任务已添加到队列"
    }

@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }

@router.get("/tasks")
async def get_user_tasks(
    current_user: User = Depends(get_current_user)
):
    tasks = task_queue.get_all_tasks()
    user_tasks = [task for task in tasks if task.data.get("user_id") == current_user.id]
    
    return [{
        "task_id": task.task_id,
        "type": task.task_type,
        "status": task.status,
        "progress": task.progress,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    } for task in user_tasks]

@router.post("/groups")
async def create_group(
    group: DouyinGroup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    groups = current_user.douyin_groups or {}
    group_id = str(uuid.uuid4())
    groups[group_id] = {
        "name": group.name,
        "accounts": group.accounts,
        "created_at": datetime.now().isoformat()
    }
    current_user.douyin_groups = groups
    db.commit()
    return {"id": group_id, **groups[group_id]}

@router.put("/groups/{group_id}")
async def update_group(
    group_id: str,
    group: DouyinGroup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    groups = current_user.douyin_groups or {}
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="分组不存在")
    
    groups[group_id].update({
        "name": group.name,
        "accounts": group.accounts,
        "updated_at": datetime.now().isoformat()
    })
    
    current_user.douyin_groups = groups
    db.commit()
    return {"id": group_id, **groups[group_id]}

@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    groups = current_user.douyin_groups or {}
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="分组不存在")
    
    del groups[group_id]
    current_user.douyin_groups = groups
    db.commit()
    return {"message": "分组已删除"}

@router.get("/groups")
async def get_groups(
    current_user: User = Depends(get_current_user)
):
    return current_user.douyin_groups or {}

@router.get("/accounts")
async def get_accounts(
    current_user: User = Depends(get_current_user)
):
    accounts = current_user.douyin_accounts or {}
    return [
        {
            "username": username,
            "status": "active" if account.get("logged_in") else "inactive"
        }
        for username, account in accounts.items()
    ]

@router.post("/schedule")
async def schedule_post(
    schedule: ScheduledPost,
    current_user: User = Depends(get_current_user)
):
    if not os.path.exists(schedule.video_path):
        raise HTTPException(status_code=400, detail="视频文件不存在")
    
    task_id = str(uuid.uuid4())
    task = Task(
        task_id=task_id,
        task_type="douyin_post",
        data={
            "accounts": schedule.accounts,
            "video_info": {
                "path": schedule.video_path,
                "title": schedule.title,
                "description": schedule.description
            },
            "user_id": current_user.id,
            "schedule_time": schedule.schedule_time
        }
    )
    
    await task_queue.add_task(task)
    
    return {
        "task_id": task_id,
        "message": "定时任务已创建",
        "schedule_time": schedule.schedule_time
    }

@router.get("/history")
async def get_post_history(
    current_user: User = Depends(get_current_user)
):
    return current_user.douyin_history or []

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user)
):
    history = current_user.douyin_history or []
    total_posts = len(history)
    success_count = sum(1 for post in history if post.get("success_count", 0) > 0)
    account_stats = {}
    
    for post in history:
        for account in post.get("accounts", []):
            if account not in account_stats:
                account_stats[account] = {"success": 0, "failed": 0}
            
            if account in post.get("success_accounts", []):
                account_stats[account]["success"] += 1
            elif account in post.get("failed_accounts", []):
                account_stats[account]["failed"] += 1
    
    success_rate = (success_count / total_posts) if total_posts > 0 else 0
    
    return DouyinStats(
        total_posts=total_posts,
        success_rate=success_rate,
        account_stats=account_stats
    )

@router.post("/preview")
async def preview_video(
    video_path: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail="视频文件不存在")
    
    # 生成预览URL（这里需要根据实际情况处理，可能需要通过nginx提供视频访问服务）
    preview_url = f"/videos/{os.path.basename(video_path)}"
    
    return {
        "preview_url": preview_url,
        "video_info": {
            "path": video_path,
            "size": os.path.getsize(video_path),
            "created": datetime.fromtimestamp(os.path.getctime(video_path)).isoformat()
        }
    }

@router.post("/preview/{filename}")
async def create_preview(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    video_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 生成预览图路径
    preview_path = os.path.join(PREVIEW_DIR, f"{os.path.splitext(filename)[0]}.jpg")
    
    try:
        # 使用ffmpeg生成预览图
        os.system(f'ffmpeg -i "{video_path}" -ss 00:00:01 -vframes 1 "{preview_path}"')
        
        return {
            "preview_url": f"/static/previews/{os.path.basename(preview_path)}",
            "video_info": {
                "path": video_path,
                "size": os.path.getsize(video_path),
                "duration": get_video_duration(video_path),
                "created": datetime.fromtimestamp(os.path.getctime(video_path)).isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成预览图失败: {str(e)}")

@router.get("/video/{filename}")
async def stream_video(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    video_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    return FileResponse(
        video_path,
        media_type=mimetypes.guess_type(filename)[0],
        filename=filename
    )

def get_video_duration(video_path: str) -> float:
    """使用ffprobe获取视频时长"""
    try:
        import subprocess
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        output = subprocess.check_output(cmd).decode().strip()
        return float(output)
    except Exception:
        return 0.0

@router.post("/batch-process-videos")
async def batch_process_videos(
    videos: List[UploadFile] = File(...),
    text: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    try:
        processed_videos = []
        for video in videos:
            # 保存原始视频
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = f"{timestamp}_{video.filename}"
            original_path = os.path.join(UPLOAD_DIR, original_filename)
            
            with open(original_path, "wb+") as file_object:
                content = await video.read()
                file_object.write(content)
            
            # 创建处理任务
            task_id = str(uuid.uuid4())
            processed_filename = f"processed_{original_filename}"
            processed_path = os.path.join(PROCESSED_DIR, processed_filename)
            
            task = Task(
                task_id=task_id,
                task_type="video_processing",
                data={
                    "original_path": original_path,
                    "processed_path": processed_path,
                    "text": text,
                    "user_id": current_user.id
                }
            )
            
            await task_queue.add_task(task)
            processed_videos.append({
                "task_id": task_id,
                "original_filename": original_filename,
                "processed_filename": processed_filename
            })
        
        return {
            "success": True,
            "message": f"{len(videos)} videos queued for processing",
            "tasks": processed_videos
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process-status/{task_id}")
async def get_process_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "status": task.status,
        "progress": task.progress,
        "result": task.result
    }