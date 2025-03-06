from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import json
import os
from datetime import datetime
import uuid
import mimetypes
from pathlib import Path
import subprocess
import asyncio
import logging
from PIL import Image, ImageDraw, ImageFont

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


@router.post("/upload")
async def upload_video_alias(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
):
    """上传视频的别名路由，重定向到/upload-video路由"""
    # 直接调用upload_video函数
    return await upload_video(file, title, description, current_user)


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
):
    try:
        # 添加关键请求日志
        logger.info(
            f"接收到视频上传请求: 用户={current_user.username}, 文件={file.filename}"
        )

        # 检查视频文件是否为空
        content = await file.read()
        file_size = len(content)

        # 重置文件指针，以便后续再次读取
        await file.seek(0)

        if file_size == 0:
            logger.error("上传的视频文件为空")
            raise HTTPException(status_code=422, detail="上传的视频文件为空")

        # 生成时间戳文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, original_filename)

        # 确定静态文件路径
        # 获取项目根目录
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )

        # 静态文件目录应该在项目根目录下
        static_dir = os.path.join(project_root, "static")
        static_videos_dir = os.path.join(static_dir, "videos")
        static_previews_dir = os.path.join(static_dir, "previews")

        # 确保静态目录存在
        os.makedirs(static_videos_dir, exist_ok=True)
        os.makedirs(static_previews_dir, exist_ok=True)

        static_video_path = os.path.join(static_videos_dir, original_filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 保存上传的视频文件
        try:
            # 文件内容已经在前面读取过了，不需要再次读取
            with open(file_path, "wb+") as file_object:
                file_object.write(content)
            logger.info(f"视频文件保存成功: {file_path}")
        except Exception as e:
            logger.error(f"保存视频文件失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"保存视频文件失败: {str(e)}")

        # 创建预览图
        preview_filename = f"{os.path.splitext(original_filename)[0]}.jpg"
        preview_path = os.path.join(static_previews_dir, preview_filename)

        # 确保预览图目录存在
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)

        # 尝试使用ffmpeg生成预览图
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
                "-y",  # 覆盖已存在的文件
                preview_path,
            ]

            # 使用subprocess.run而不是subprocess.check_output，以便获取更详细的错误信息
            process = subprocess.run(cmd, capture_output=True, text=True)

            if process.returncode != 0:
                logger.error(f"生成预览图失败，返回码: {process.returncode}")

                # 尝试使用不同的参数重新生成
                alt_cmd = [
                    ffmpeg_path,
                    "-i",
                    file_path,
                    "-ss",
                    "00:00:00.5",  # 使用不同的时间点
                    "-vframes",
                    "1",
                    "-y",  # 覆盖已存在的文件
                    preview_path,
                ]

                alt_process = subprocess.run(alt_cmd, capture_output=True, text=True)

                if alt_process.returncode != 0:
                    logger.error(f"备选命令也失败，返回码: {alt_process.returncode}")
                    # 使用默认预览图
                    use_default_preview = True
                else:
                    use_default_preview = False
            else:
                use_default_preview = False

            # 检查预览图是否成功生成
            if not os.path.exists(preview_path) or os.path.getsize(preview_path) == 0:
                logger.error(f"预览图生成失败或为空: {preview_path}")
                use_default_preview = True
            else:
                logger.info(f"预览图生成成功: {preview_path}")
                use_default_preview = False

        except Exception as e:
            logger.error(f"生成预览图时发生错误: {str(e)}")
            # 使用默认预览图
            use_default_preview = True

        # 复制文件到静态目录
        try:
            import shutil

            # 复制文件
            shutil.copy2(file_path, static_video_path)

            # 验证文件是否成功复制
            if not os.path.exists(static_video_path):
                logger.error(f"复制后文件不存在: {static_video_path}")

        except Exception as e:
            logger.error(f"复制文件到静态目录失败: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"复制文件到静态目录失败: {str(e)}"
            )

        # 如果需要使用默认预览图
        if use_default_preview:
            try:
                default_preview = os.path.join(
                    project_root,
                    "static",
                    "default_preview.jpg",
                )
                if os.path.exists(default_preview):
                    import shutil

                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
                    # 复制默认预览图
                    shutil.copy2(default_preview, preview_path)
                    logger.info(f"已使用默认预览图")
                else:
                    logger.error(f"默认预览图不存在: {default_preview}")
                    # 创建一个简单的默认图片
                    try:
                        from PIL import Image, ImageDraw

                        img = Image.new("RGB", (480, 270), color=(240, 240, 240))
                        d = ImageDraw.Draw(img)
                        d.text(
                            (240, 135),
                            "预览图生成失败",
                            fill=(128, 128, 128),
                        )
                        img.save(preview_path)
                        logger.info(f"已创建简单的默认预览图")
                    except Exception as e:
                        logger.error(f"创建简单的默认预览图失败: {str(e)}")
            except Exception as e:
                logger.error(f"使用默认预览图失败: {str(e)}")

        preview_url = f"/static/previews/{preview_filename}"
        video_url = f"/static/videos/{original_filename}"
        logger.info(f"上传成功，预览URL: {preview_url}")

        # 检查视频文件是否存在
        if not os.path.exists(static_video_path):
            logger.error(f"静态视频文件不存在: {static_video_path}")
            raise HTTPException(
                status_code=500, detail="视频文件复制失败，请检查服务器日志"
            )

        # 确保返回正确的字段
        response_data = {
            "success": True,
            "file_path": file_path,
            "saved_path": file_path,  # 添加saved_path字段
            "preview_url": preview_url,
            "video_url": video_url,
            "title": title,
            "description": description,
            "filename": os.path.basename(file_path),  # 添加filename字段
        }

        return response_data

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

    # 不再使用 douyin_history 字段，直接添加任务到队列
    # history = current_user.douyin_history or []
    # history.append(
    #     {
    #         "task_id": task_id,
    #         "video_id": str(uuid.uuid4()),  # 临时视频ID
    #         "title": title,
    #         "description": description,
    #         "accounts": accounts,
    #         "success_count": 0,
    #         "failed_count": 0,
    #         "created_at": datetime.now().isoformat(),
    #         "status": "pending",
    #         "retries": 0,
    #     }
    # )
    # current_user.douyin_history = history
    # db.commit()

    await task_queue.add_task(task)

    return {"task_id": task_id, "message": "任务已添加到队列"}


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 确定任务结果
    task_result = "unknown"
    if task.status == TaskStatus.COMPLETED and not task.error:
        task_result = "success"
    elif task.status == TaskStatus.FAILED or task.error:
        task_result = "failed"

    response = {
        "task_id": task.task_id,
        "type": task.task_type,  # 添加任务类型
        "status": task.status,
        "result": task_result,  # 添加任务结果状态
        "progress": task.progress,
        "error": task.error,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "retry_count": task.retry_count,  # 添加重试次数
        "data": task.data,  # 添加任务数据
    }

    # 如果有结果数据，添加到响应中
    if task.result:
        response["result_data"] = task.result

    return response


@router.get("/tasks")
async def get_user_tasks(
    status: str = None,
    type: str = None,
    result: str = None,
    current_user: User = Depends(get_current_user),
):
    """
    获取用户的任务列表
    - status: 任务状态过滤（pending, scheduled, running, completed）
    - type: 任务类型过滤（video_processing, douyin_post）
    - result: 任务结果过滤（success, failed）
    """
    tasks = task_queue.get_all_tasks()
    result = []

    # 过滤任务
    for task in tasks:
        # 检查任务是否属于当前用户
        task_user_id = task.data.get("user_id")
        if task_user_id != current_user.id:
            continue

        # 根据状态过滤
        if status:
            status_list = status.split(",")
            if task.status not in status_list:
                continue

        # 根据类型过滤
        if type and task.task_type != type:
            continue

        # 根据结果过滤
        if result:
            # 确定任务结果
            task_result = "success"
            if task.error or (
                isinstance(task.result, dict) and task.result.get("error")
            ):
                task_result = "failed"

            if task_result != result:
                continue

        # 确定任务结果状态
        task_result = "success"
        if task.error or (isinstance(task.result, dict) and task.result.get("error")):
            task_result = "failed"

        # 构建任务信息
        task_info = {
            "task_id": task.task_id,
            "type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "error": task.error,
            "result": task_result,  # 添加结果状态
            "retry_count": task.retry_count,  # 添加重试次数
        }

        # 添加特定任务类型的信息
        if task.task_type == "video_processing":
            task_info.update(
                {
                    "original_filename": os.path.basename(
                        task.data.get("original_path", "")
                    ),
                    "text": task.data.get("text", ""),
                    "remove_subtitles": task.data.get("remove_subtitles", False),
                    "generate_subtitles": task.data.get("generate_subtitles", False),
                }
            )

            # 如果任务已完成，添加下载链接
            if task.status == TaskStatus.COMPLETED and task.result:
                task_info.update(
                    {
                        "download_url": f"/api/v1/douyin/processed-video/{task.task_id}",
                        "thumbnail_url": f"/api/v1/douyin/processed-video-thumbnail/{task.task_id}",
                        "filename": os.path.basename(
                            task.result.get("processed_path", "")
                        ),
                    }
                )

        result.append(task_info)

    return result


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


@router.get("/task-history")
async def get_task_history(current_user: User = Depends(get_current_user)):
    """
    获取用户的任务历史记录（已弃用）

    此接口已弃用，请使用 /tasks?status=completed 接口代替
    """
    # 重定向到 get_user_tasks 函数，获取已完成的任务
    return await get_user_tasks(status="completed", current_user=current_user)


@router.get("/history")
async def get_post_history(current_user: User = Depends(get_current_user)):
    """
    获取历史任务记录（已弃用）

    此接口已弃用，请使用 /tasks?status=completed 接口代替
    """
    # 重定向到 get_user_tasks 函数，获取已完成的任务
    return await get_user_tasks(status="completed", current_user=current_user)


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    """获取任务统计信息"""
    # 获取所有任务
    all_tasks = await get_user_tasks(current_user=current_user)

    # 统计信息
    total_tasks = len(all_tasks)
    completed_tasks = sum(
        1 for task in all_tasks if task.get("status") == TaskStatus.COMPLETED
    )
    failed_tasks = sum(
        1 for task in all_tasks if task.get("status") == TaskStatus.FAILED
    )
    running_tasks = sum(
        1 for task in all_tasks if task.get("status") == TaskStatus.RUNNING
    )

    # 按类型统计
    task_types = {}
    for task in all_tasks:
        task_type = task.get("type")
        if task_type not in task_types:
            task_types[task_type] = 0
        task_types[task_type] += 1

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "running_tasks": running_tasks,
        "task_types": task_types,
    }


@router.post("/preview")
async def preview_video(
    video_path: str = Form(...), current_user: User = Depends(get_current_user)
):
    logger.info(f"生成预览图请求: {video_path}")

    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        raise HTTPException(status_code=400, detail="视频文件不存在")

    # 确保预览目录存在
    os.makedirs(PREVIEW_DIR, exist_ok=True)

    # 生成预览图
    preview_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}.jpg"
    preview_path = os.path.join(PREVIEW_DIR, preview_filename)
    logger.info(f"预览图路径: {preview_path}")

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
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"命令执行结果: {result.returncode}")

        if not os.path.exists(preview_path) or os.path.getsize(preview_path) == 0:
            logger.error(f"预览图生成失败，文件不存在或为空: {preview_path}")
            raise HTTPException(
                status_code=500, detail="预览图生成失败，请检查视频格式"
            )

        # 获取视频信息
        duration = get_video_duration(video_path)
        file_size = os.path.getsize(video_path)

        # 生成预览和视频的URL
        preview_url = f"/static/previews/{preview_filename}"
        video_url = f"/static/videos/{os.path.basename(video_path)}"

        logger.info(f"预览URL: {preview_url}, 视频URL: {video_url}")

        # 获取服务器基础URL
        base_url = "http://localhost:8000"  # 默认本地开发环境

        return {
            "success": True,
            "preview_url": f"{base_url}{preview_url}",
            "video_url": f"{base_url}{video_url}",
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
    except subprocess.CalledProcessError as e:
        error_msg = f"ffmpeg命令执行失败: {e.stderr.decode() if e.stderr else str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"生成预览失败: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/video/{filename}")
async def stream_video(filename: str, current_user: User = Depends(get_current_user)):
    logger.info(f"获取视频请求: {filename}")

    # 首先检查上传目录
    video_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(video_path):
        # 如果上传目录中不存在，检查静态目录
        static_video_path = os.path.join("static/videos", filename)
        if os.path.exists(static_video_path):
            video_path = static_video_path
            logger.info(f"在静态目录中找到视频: {video_path}")
        else:
            logger.error(f"视频文件不存在: {video_path} 或 {static_video_path}")
            raise HTTPException(status_code=404, detail="视频文件不存在")

    # 获取文件大小
    file_size = os.path.getsize(video_path)
    logger.info(f"返回视频: {video_path}, 大小: {file_size} 字节")

    # 获取正确的MIME类型
    content_type = mimetypes.guess_type(filename)[0]
    if not content_type:
        content_type = "video/mp4"  # 默认为MP4

    logger.info(f"视频内容类型: {content_type}")

    # 设置响应头，支持范围请求
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Cache-Control": "public, max-age=3600",
        "Content-Disposition": f'inline; filename="{filename}"',
        "Access-Control-Allow-Origin": "*",  # 允许跨域访问
    }

    # 对于小视频文件，直接返回内容
    if file_size < 10 * 1024 * 1024:  # 小于10MB的文件
        with open(video_path, "rb") as f:
            content = f.read()

        return Response(content=content, media_type=content_type, headers=headers)

    # 对于大文件，仍然使用FileResponse
    return FileResponse(
        video_path,
        media_type=content_type,
        filename=filename,
        headers=headers,
    )


@router.get("/preview/{filename}")
async def get_preview_image(
    filename: str, current_user: User = Depends(get_current_user)
):
    logger.info(f"获取预览图请求: {filename}")
    preview_path = os.path.join(PREVIEW_DIR, filename)

    if not os.path.exists(preview_path):
        logger.error(f"预览图不存在: {preview_path}")
        # 尝试查找类似名称的文件
        dir_files = os.listdir(PREVIEW_DIR)
        similar_files = [f for f in dir_files if filename.lower() in f.lower()]
        if similar_files:
            logger.info(f"找到类似名称的文件: {similar_files}")
            return {
                "error": "预览图不存在",
                "similar_files": similar_files,
                "requested_file": filename,
            }
        raise HTTPException(status_code=404, detail="预览图不存在")

    file_size = os.path.getsize(preview_path)
    if file_size == 0:
        logger.error(f"预览图文件为空: {preview_path}")
        raise HTTPException(status_code=500, detail="预览图文件为空")

    logger.info(f"返回预览图: {preview_path}, 大小: {file_size} 字节")

    # 设置响应头，确保正确的缓存控制和内容类型
    headers = {
        "Cache-Control": "public, max-age=3600",
        "Content-Disposition": f'inline; filename="{filename}"',
        "Content-Type": "image/jpeg",
        "Access-Control-Allow-Origin": "*",  # 允许跨域访问
    }

    # 直接读取文件内容并返回，而不是使用FileResponse
    with open(preview_path, "rb") as f:
        content = f.read()

    return Response(content=content, media_type="image/jpeg", headers=headers)


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
    processing_mode: str = Form("cloud"),  # 新增处理模式参数，默认为云服务处理
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
                    "auto_detect": auto_detect_subtitles,
                    "processing_mode": processing_mode,  # 添加处理模式到任务数据中
                    "user_id": current_user.id,  # 将 user_id 移到 data 字典中
                },
            )

            # 保存任务到数据库
            logger.info(
                f"创建任务: ID={task_id}, 类型={task.task_type}, 用户ID={current_user.id}"
            )
            await task_queue.add_task(task)
            logger.info(f"任务已添加到队列: ID={task_id}")

            processed_videos.append(
                {
                    "task_id": task_id,
                    "original_filename": original_filename,
                    "processed_filename": processed_filename,
                }
            )

        return {"success": True, "tasks": processed_videos}
    except Exception as e:
        logger.error(f"批量处理视频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量处理视频失败: {str(e)}")


@router.get("/process-status/{task_id}")
async def get_process_status(
    task_id: str, current_user: User = Depends(get_current_user)
):
    """获取任务处理状态的详细信息"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 确定任务结果
    task_result = "unknown"
    if task.status == TaskStatus.COMPLETED and not task.error:
        task_result = "success"
    elif task.status == TaskStatus.FAILED or task.error:
        task_result = "failed"

    response = {
        "task_id": task.task_id,
        "type": task.task_type,  # 添加任务类型
        "status": task.status,
        "result": task_result,  # 添加任务结果状态
        "progress": task.progress,
        "error": task.error,
        "created_at": (
            task.created_at.isoformat()
            if hasattr(task.created_at, "isoformat")
            else task.created_at
        ),
        "updated_at": (
            task.updated_at.isoformat()
            if hasattr(task.updated_at, "isoformat")
            else task.updated_at
        ),
        "retry_count": task.retry_count,  # 添加重试次数
    }

    # 添加任务数据的安全副本（排除敏感信息）
    if task.data:
        safe_data = task.data.copy()
        # 排除可能的敏感信息
        if "password" in safe_data:
            safe_data.pop("password")
        if "token" in safe_data:
            safe_data.pop("token")
        response["data"] = safe_data

    # 如果有结果数据，添加到响应中
    if task.result:
        response["result_data"] = task.result

    return response


@router.get("/processed-video/{task_id}")
async def get_processed_video(
    task_id: str, current_user: User = Depends(get_current_user)
):
    """获取处理后的视频文件，用于下载"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task.result or "processed_path" not in task.result:
        raise HTTPException(status_code=404, detail="处理结果不存在")

    processed_path = task.result["processed_path"]
    if not os.path.exists(processed_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    filename = os.path.basename(processed_path)

    return FileResponse(
        path=processed_path,
        filename=filename,
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/processed-video-thumbnail/{task_id}")
async def get_processed_video_thumbnail(
    task_id: str, current_user: User = Depends(get_current_user)
):
    """获取处理后视频的缩略图"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task.result or "processed_path" not in task.result:
        raise HTTPException(status_code=404, detail="处理结果不存在")

    processed_path = task.result["processed_path"]
    if not os.path.exists(processed_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    # 生成缩略图文件名
    thumbnail_filename = (
        f"thumbnail_{os.path.basename(processed_path).replace('.mp4', '.jpg')}"
    )
    thumbnail_path = os.path.join(PREVIEW_DIR, thumbnail_filename)

    # 如果缩略图不存在，则生成
    if not os.path.exists(thumbnail_path):
        try:
            # 使用ffmpeg生成缩略图
            cmd = [
                "ffmpeg",
                "-i",
                processed_path,
                "-ss",
                "00:00:01",  # 从视频的第1秒截取
                "-vframes",
                "1",
                "-vf",
                "scale=320:-1",  # 缩放到宽度320，高度按比例
                thumbnail_path,
            ]
            subprocess.run(cmd, check=True)
        except Exception as e:
            logger.error(f"生成缩略图失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"生成缩略图失败: {str(e)}")

    # 设置响应头
    headers = {
        "Cache-Control": "public, max-age=3600",
        "Content-Disposition": f'inline; filename="{thumbnail_filename}"',
        "Content-Type": "image/jpeg",
    }

    # 返回缩略图
    return FileResponse(path=thumbnail_path, media_type="image/jpeg", headers=headers)


@router.get("/check-local-processing", response_model=Dict[str, bool])
async def check_local_processing(current_user: User = Depends(get_current_user)):
    """
    检查本地处理是否可用

    目前本地处理功能尚未实现，所以始终返回False
    """
    # TODO: 实现检查本地GPU和依赖是否可用的逻辑
    return {"available": False}


@router.post("/upload-video-v1")
async def upload_video_v1(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
):
    """上传视频的v1版本路由"""
    return await upload_video(file, title, description, current_user)


@router.post("/upload-video-with-preview")
async def upload_video_with_preview(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user),
):
    """上传视频并生成预览图的专用路由"""
    return await upload_video(file, title, description, current_user)


@router.get("/debug/tasks")
async def debug_tasks(current_user: User = Depends(get_current_user)):
    """
    调试端点，用于查看所有任务的状态
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以访问此端点")

    tasks = task_queue.get_all_tasks()
    result = []

    for task in tasks:
        task_info = {
            "task_id": task.task_id,
            "type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "error": task.error,
            "retry_count": task.retry_count,
            "user_id": task.data.get("user_id"),
        }
        result.append(task_info)

    return result
