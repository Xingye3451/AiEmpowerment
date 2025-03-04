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
import logging

from app.core.deps import get_db, get_current_user
from app.schemas.user import (
    BatchDouyinLogin,
    BatchDouyinLoginResponse,
    BatchDouyinPost,
    BatchDouyinPostResponse,
    DouyinLoginResponse,
    DouyinPostResponse,
    DouyinGroup,
    ScheduledPost,
    DouyinStats,
)
from app.models.user import User
from app.core.task_queue import TaskQueue, Task, TaskStatus

logger = logging.getLogger(__name__)

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
    db: Session = Depends(get_db),
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
                    "logged_in": True,
                }

            results.append(
                DouyinLoginResponse(
                    username=account.username,
                    success=success,
                    error=None if success else "登录失败",
                )
            )
        except Exception as e:
            results.append(
                DouyinLoginResponse(
                    username=account.username, success=False, error=str(e)
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
    current_user: User = Depends(get_current_user),
):
    try:
        # 生成时间戳文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = f"{timestamp}_{video.filename}"
        file_path = os.path.join(UPLOAD_DIR, original_filename)
        static_video_path = os.path.join("static/videos", original_filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        os.makedirs(os.path.dirname(static_video_path), exist_ok=True)

        # 保存上传的视频文件
        try:
            content = await video.read()
            with open(file_path, "wb+") as file_object:
                file_object.write(content)
        except Exception as e:
            logger.error(f"保存视频文件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"保存视频文件失败: {str(e)}")

        # 创建预览图
        preview_filename = f"{os.path.splitext(original_filename)[0]}.jpg"
        preview_path = os.path.join(PREVIEW_DIR, preview_filename)

        try:
            # 检查是否安装了ffmpeg
            try:
                ffmpeg_path = (
                    subprocess.check_output(["which", "ffmpeg"]).decode().strip()
                )
            except subprocess.CalledProcessError:
                # 如果找不到ffmpeg，尝试使用常见的安装路径
                common_paths = [
                    "/usr/local/bin/ffmpeg",
                    "/opt/homebrew/bin/ffmpeg",
                    "/usr/bin/ffmpeg",
                ]
                ffmpeg_path = None
                for path in common_paths:
                    if os.path.exists(path):
                        ffmpeg_path = path
                        break

                if not ffmpeg_path:
                    logger.error("找不到ffmpeg，请确保已安装")
                    raise HTTPException(
                        status_code=500, detail="服务器未安装ffmpeg，请联系管理员安装"
                    )

            # 使用ffmpeg生成预览图
            cmd = [
                ffmpeg_path,
                "-i",
                file_path,
                "-ss",
                "00:00:01",
                "-vframes",
                "1",
                "-vf",
                "scale=480:-1",
                preview_path,
            ]
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if process.returncode != 0:
                logger.error(f"生成预览图失败: {process.stderr}")
                raise HTTPException(
                    status_code=500, detail=f"生成预览图失败: {process.stderr}"
                )

        except subprocess.CalledProcessError as e:
            logger.error(f"执行ffmpeg命令失败: {e.stderr}")
            raise HTTPException(status_code=500, detail=f"生成预览图失败: {e.stderr}")
        except Exception as e:
            logger.error(f"生成预览图时发生错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"生成预览图失败: {str(e)}")

        # 复制文件到静态目录而不是创建软链接
        try:
            import shutil

            shutil.copy2(file_path, static_video_path)
        except Exception as e:
            logger.error(f"复制文件到静态目录失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"复制文件到静态目录失败: {str(e)}"
            )

        return {
            "success": True,
            "file_path": file_path,
            "preview_url": f"/static/previews/{preview_filename}",
            "video_url": f"/static/videos/{original_filename}",
            "title": title,
            "description": description,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理视频上传请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 更新原有的batch_post路由以支持发布历史记录
@router.post("/batch-post")
async def batch_post_video(
    accounts: List[str] = Form(...),
    video_path: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
                "description": description,
            },
            "user_id": current_user.id,
        },
    )

    # 创建历史记录
    history = current_user.douyin_history or []
    history.append(
        {
            "task_id": task_id,
            "video_id": str(uuid.uuid4()),  # 临时视频ID
            "title": title,
            "description": description,
            "accounts": accounts,
            "success_count": 0,
            "failed_count": 0,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "retries": 0,
        }
    )
    current_user.douyin_history = history
    db.commit()

    await task_queue.add_task(task)

    return {"task_id": task_id, "message": "任务已添加到队列"}


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
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
        "updated_at": task.updated_at,
    }


@router.get("/tasks")
async def get_user_tasks(current_user: User = Depends(get_current_user)):
    tasks = task_queue.get_all_tasks()
    user_tasks = [task for task in tasks if task.data.get("user_id") == current_user.id]

    return [
        {
            "task_id": task.task_id,
            "type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
        for task in user_tasks
    ]


@router.post("/groups")
async def create_group(
    group: DouyinGroup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = current_user.douyin_groups or {}
    group_id = str(uuid.uuid4())
    groups[group_id] = {
        "name": group.name,
        "accounts": group.accounts,
        "created_at": datetime.now().isoformat(),
    }
    current_user.douyin_groups = groups
    db.commit()
    return {"id": group_id, **groups[group_id]}


@router.put("/groups/{group_id}")
async def update_group(
    group_id: str,
    group: DouyinGroup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = current_user.douyin_groups or {}
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="分组不存在")

    groups[group_id].update(
        {
            "name": group.name,
            "accounts": group.accounts,
            "updated_at": datetime.now().isoformat(),
        }
    )

    current_user.douyin_groups = groups
    db.commit()
    return {"id": group_id, **groups[group_id]}


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = current_user.douyin_groups or {}
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="分组不存在")

    del groups[group_id]
    current_user.douyin_groups = groups
    db.commit()
    return {"message": "分组已删除"}


@router.get("/groups")
async def get_groups(current_user: User = Depends(get_current_user)):
    return current_user.douyin_groups or {}


@router.get("/accounts")
async def get_accounts(current_user: User = Depends(get_current_user)):
    accounts = current_user.douyin_accounts or {}
    return [
        {
            "username": username,
            "status": "active" if account.get("logged_in") else "inactive",
        }
        for username, account in accounts.items()
    ]


@router.post("/schedule")
async def schedule_post(
    schedule: ScheduledPost, current_user: User = Depends(get_current_user)
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
                "description": schedule.description,
            },
            "user_id": current_user.id,
            "schedule_time": schedule.schedule_time,
        },
    )

    await task_queue.add_task(task)

    return {
        "task_id": task_id,
        "message": "定时任务已创建",
        "schedule_time": schedule.schedule_time,
    }


@router.get("/history")
async def get_post_history(current_user: User = Depends(get_current_user)):
    return current_user.douyin_history or []


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
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
        total_posts=total_posts, success_rate=success_rate, account_stats=account_stats
    )


@router.post("/preview")
async def preview_video(
    video_path: str = Form(...), current_user: User = Depends(get_current_user)
):
    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail="视频文件不存在")

    # 生成预览图
    preview_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}.jpg"
    preview_path = os.path.join(PREVIEW_DIR, preview_filename)

    try:
        # 使用ffmpeg生成预览图
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-ss",
            "00:00:01",  # 从第1秒开始
            "-vframes",
            "1",
            "-vf",
            "scale=480:-1",  # 将宽度调整为480，高度按比例缩放
            preview_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        # 获取视频信息
        duration = get_video_duration(video_path)
        file_size = os.path.getsize(video_path)

        # 生成预览和视频的URL
        preview_url = f"/static/previews/{preview_filename}"
        video_url = f"/static/videos/{os.path.basename(video_path)}"

        return {
            "success": True,
            "preview_url": preview_url,
            "video_url": video_url,
            "video_info": {
                "path": video_path,
                "size": file_size,
                "duration": duration,
                "filename": os.path.basename(video_path),
                "created": datetime.fromtimestamp(
                    os.path.getctime(video_path)
                ).isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"生成预览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成预览失败: {str(e)}")


@router.get("/video/{filename}")
async def stream_video(filename: str, current_user: User = Depends(get_current_user)):
    video_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    # 获取文件大小
    file_size = os.path.getsize(video_path)

    # 设置响应头，支持范围请求
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Cache-Control": "public, max-age=3600",
        "Content-Disposition": f'inline; filename="{filename}"',
    }

    return FileResponse(
        video_path,
        media_type=mimetypes.guess_type(filename)[0],
        filename=filename,
        headers=headers,
    )


@router.get("/preview/{filename}")
async def get_preview_image(
    filename: str, current_user: User = Depends(get_current_user)
):
    preview_path = os.path.join(PREVIEW_DIR, filename)
    if not os.path.exists(preview_path):
        raise HTTPException(status_code=404, detail="预览图不存在")

    return FileResponse(
        preview_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )


def get_video_duration(video_path: str) -> float:
    """使用ffprobe获取视频时长"""
    try:
        import subprocess

        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        output = subprocess.check_output(cmd).decode().strip()
        return float(output)
    except Exception:
        return 0.0


@router.post("/batch-process-videos")
async def batch_process_videos(
    videos: List[UploadFile] = File(...),
    text: str = Form(...),
    remove_subtitles: bool = Form(True),
    generate_subtitles: bool = Form(False),
    video_areas: List[str] = Form(None),  # 现在是可选的
    auto_detect_subtitles: bool = Form(False),  # 新增自动检测选项
    current_user: User = Depends(get_current_user),
):
    try:
        processed_videos = []
        for i, video in enumerate(videos):
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

            # 解析区域选择数据（如果提供）
            selected_area = None
            if video_areas and i < len(video_areas):
                try:
                    selected_area = json.loads(video_areas[i])
                except json.JSONDecodeError:
                    logger.warning(f"无法解析视频 {original_filename} 的区域选择数据")

            task = Task(
                task_id=task_id,
                task_type="video_processing",
                data={
                    "original_path": original_path,
                    "processed_path": processed_path,
                    "text": text,
                    "remove_subtitles": remove_subtitles,
                    "generate_subtitles": generate_subtitles,
                    "selected_area": selected_area,
                    "auto_detect_subtitles": auto_detect_subtitles,  # 添加自动检测选项
                    "user_id": current_user.id,
                },
            )

            await task_queue.add_task(task)
            processed_videos.append(
                {
                    "task_id": task_id,
                    "original_filename": original_filename,
                    "processed_filename": processed_filename,
                }
            )

        return {
            "success": True,
            "message": f"{len(videos)} videos queued for processing",
            "tasks": processed_videos,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/process-status/{task_id}")
async def get_process_status(
    task_id: str, current_user: User = Depends(get_current_user)
):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"status": task.status, "progress": task.progress, "result": task.result}
