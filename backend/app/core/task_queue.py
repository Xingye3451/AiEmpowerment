from typing import Dict, List, Optional
import asyncio
from datetime import datetime, timedelta
import heapq
from dataclasses import dataclass, field
import logging
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, AsyncSessionLocal
from app.models.user import User
from app.core.config import settings
import os
import subprocess
import shutil
from app.core.ai_services import VideoProcessor
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.notification_service import NotificationService
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate
from app.models.task import Task as DBTask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus:
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass(order=True)
class ScheduledTask:
    schedule_time: datetime
    task: "Task" = field(compare=False)


class Task:
    def __init__(self, task_id: str, task_type: str, data: dict):
        self.task_id = task_id
        self.task_type = task_type
        self.data = data
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.retry_count = 0
        self.max_retries = settings.MAX_RETRY_COUNT
        self.last_retry = None
        self.schedule_time = data.get("schedule_time")


class TaskQueue:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskQueue, cls).__new__(cls)
            cls._instance.tasks: Dict[str, Task] = {}
            cls._instance.queue = asyncio.Queue()
            cls._instance.scheduled_tasks: List[ScheduledTask] = []
            cls._instance.retry_delays = settings.RETRY_DELAY
            cls._instance.history_cleanup_interval = 7 * 24 * 60 * 60  # 7天
            cls._instance.running = False
            cls._instance.initialized = False
        return cls._instance

    async def initialize(self):
        """初始化任务队列，从数据库加载任务"""
        if self.initialized:
            return

        logger.info("初始化任务队列，从数据库加载任务")

        try:
            async with AsyncSessionLocal() as db:
                # 加载未完成的任务
                pending_tasks = await TaskService.get_tasks(
                    db,
                    status=f"{TaskStatus.PENDING},{TaskStatus.SCHEDULED},{TaskStatus.RUNNING},{TaskStatus.RETRYING}",
                )

                for db_task in pending_tasks:
                    task = Task(
                        task_id=db_task.id,
                        task_type=db_task.task_type,
                        data=db_task.data,
                    )
                    task.status = db_task.status
                    task.progress = db_task.progress
                    task.result = db_task.result
                    task.error = db_task.error
                    task.created_at = db_task.created_at
                    task.updated_at = db_task.updated_at
                    task.retry_count = db_task.retry_count
                    task.max_retries = db_task.max_retries
                    task.last_retry = db_task.last_retry_at
                    task.schedule_time = db_task.scheduled_at

                    self.tasks[task.task_id] = task

                    # 如果是定时任务且时间未到，加入定时队列
                    if (
                        task.status == TaskStatus.SCHEDULED
                        and task.schedule_time
                        and task.schedule_time > datetime.now()
                    ):
                        heapq.heappush(
                            self.scheduled_tasks,
                            ScheduledTask(task.schedule_time, task),
                        )
                    # 否则加入普通队列
                    elif task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
                        await self.queue.put(task)

                logger.info(f"从数据库加载了 {len(pending_tasks)} 个未完成的任务")

            self.initialized = True

            # 启动任务处理循环
            if not self.running:
                logger.info("启动任务处理循环")
                self.running = True
                asyncio.create_task(self.process_tasks())
                asyncio.create_task(self.process_scheduled_tasks())
                asyncio.create_task(self.cleanup_old_tasks())

        except Exception as e:
            logger.error(f"初始化任务队列失败: {e}")

    async def add_task(
        self,
        task_id: str = None,
        task_type: str = None,
        data: dict = None,
        scheduled_at=None,
        callback=None,
    ) -> str:
        """添加任务到队列"""
        # 如果传入的是Task对象
        if isinstance(task_id, Task):
            task = task_id
            logger.info(f"添加任务到队列: ID={task.task_id}, 类型={task.task_type}")
        else:
            # 创建新的Task对象
            task = Task(task_id=task_id, task_type=task_type, data=data)
            if scheduled_at:
                task.schedule_time = scheduled_at
            logger.info(f"添加任务到队列: ID={task.task_id}, 类型={task.task_type}")

        # 确保已初始化
        if not self.initialized:
            await self.initialize()

        self.tasks[task.task_id] = task

        # 保存到数据库
        try:
            async with AsyncSessionLocal() as db:
                # 检查任务是否已存在
                existing_task = await TaskService.get_task(db, task.task_id)
                if existing_task:
                    logger.info(f"任务已存在: ID={task.task_id}")
                    # 更新任务
                    task_update = TaskUpdate(
                        status=task.status,
                        progress=task.progress,
                        result=task.result,
                        error=task.error,
                        retry_count=task.retry_count,
                        scheduled_at=task.schedule_time,
                    )
                    await TaskService.update_task(db, task.task_id, task_update)
                else:
                    # 创建新任务
                    task_create = TaskCreate(
                        task_type=task.task_type,
                        data=task.data,
                        user_id=task.data.get("user_id"),
                        scheduled_at=task.schedule_time,
                        max_retries=task.max_retries,
                    )
                    db_task = await TaskService.create_task(db, task_create)
                    # 更新任务ID
                    if task.task_id != db_task.id:
                        old_task_id = task.task_id
                        task.task_id = db_task.id
                        self.tasks[db_task.id] = task
                        if old_task_id in self.tasks:
                            del self.tasks[old_task_id]
        except Exception as e:
            logger.error(f"保存任务到数据库失败: {e}")

        if task.schedule_time and task.schedule_time > datetime.now():
            # 如果是定时任务且时间未到，加入定时队列
            task.status = TaskStatus.SCHEDULED
            logger.info(f"任务 {task.task_id} 已调度，将在 {task.schedule_time} 执行")
            heapq.heappush(
                self.scheduled_tasks, ScheduledTask(task.schedule_time, task)
            )

            # 更新数据库中的任务状态
            try:
                async with AsyncSessionLocal() as db:
                    task_update = TaskUpdate(status=TaskStatus.SCHEDULED)
                    await TaskService.update_task(db, task.task_id, task_update)
            except Exception as e:
                logger.error(f"更新任务状态失败: {e}")
        else:
            # 否则直接加入普通队列
            logger.info(f"任务 {task.task_id} 已加入执行队列")
            await self.queue.put(task)

        if not self.running:
            logger.info("启动任务处理循环")
            self.running = True
            asyncio.create_task(self.process_tasks())
            asyncio.create_task(self.process_scheduled_tasks())
            asyncio.create_task(self.cleanup_old_tasks())

        logger.info(f"任务添加完成: ID={task.task_id}")
        return task.task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self.tasks.values())

    def update_task_status(
        self,
        task_id: str,
        status: str = None,
        progress: int = None,
        result: dict = None,
        error: str = None,
        message: str = None,
        current_stage: str = None,
        **kwargs,
    ):
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 任务状态
            progress: 进度值（0-100）
            result: 结果数据
            error: 错误信息
            message: 进度消息
            current_stage: 当前处理阶段
            **kwargs: 其他参数
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"尝试更新不存在的任务: {task_id}")
            return

        old_status = task.status

        if status:
            task.status = status
            if old_status != status:
                logger.info(f"任务状态变更: ID={task_id}, {old_status} -> {status}")

        if progress is not None:
            task.progress = progress

        if message:
            task.message = message

        if current_stage:
            if not hasattr(task, "data") or task.data is None:
                task.data = {}
            task.data["current_stage"] = current_stage

        if result:
            task.result = result

        if error:
            task.error = error
            logger.error(f"任务错误: ID={task_id}, 错误={error}")

        for key, value in kwargs.items():
            setattr(task, key, value)

        task.updated_at = datetime.now()

        # 更新数据库中的任务状态
        try:
            asyncio.create_task(self._update_task_in_db(task))
        except Exception as e:
            logger.error(f"更新任务状态到数据库失败: {e}")

    async def _update_task_in_db(self, task: Task):
        """更新数据库中的任务"""
        from app.services.task_service import TaskService
        from app.schemas.task import TaskUpdate

        try:
            async with AsyncSessionLocal() as db:
                # 如果任务有进度和当前阶段信息，使用新的update_task_progress方法
                if hasattr(task, "progress") and (
                    hasattr(task, "message")
                    or (
                        hasattr(task, "data")
                        and task.data
                        and "current_stage" in task.data
                    )
                ):
                    current_stage = (
                        task.data.get("current_stage")
                        if hasattr(task, "data") and task.data
                        else None
                    )
                    message = task.message if hasattr(task, "message") else None

                    await TaskService.update_task_progress(
                        db,
                        task.task_id,
                        task.progress,
                        current_stage=current_stage,
                        message=message,
                    )

                # 对于其他更新，使用常规的update_task方法
                update_data = {
                    "status": task.status,
                    "progress": task.progress,
                    "result": task.result,
                    "error": task.error,
                    "data": task.data,
                    "retry_count": task.retry_count,
                }

                task_update = TaskUpdate(**update_data)
                await TaskService.update_task(db, task.task_id, task_update)
        except Exception as e:
            logger.error(f"更新任务到数据库失败: {e}", exc_info=True)

    async def cleanup_old_tasks(self):
        """定期清理旧任务"""
        while True:
            try:
                now = datetime.now()
                old_tasks = [
                    task_id
                    for task_id, task in self.tasks.items()
                    if (now - task.updated_at).days >= 7
                    and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
                ]

                for task_id in old_tasks:
                    del self.tasks[task_id]

                logger.info(f"清理了 {len(old_tasks)} 个旧任务")

                # 注意：我们不从数据库中删除旧任务，以便保留历史记录
            except Exception as e:
                logger.error(f"清理旧任务失败: {e}")

            await asyncio.sleep(self.history_cleanup_interval)

    async def process_scheduled_tasks(self):
        """处理定时任务"""
        while True:
            try:
                now = datetime.now()

                # 检查是否有定时任务需要执行
                while (
                    self.scheduled_tasks
                    and self.scheduled_tasks[0].schedule_time <= now
                ):
                    scheduled_task = heapq.heappop(self.scheduled_tasks)
                    task = scheduled_task.task

                    logger.info(
                        f"定时任务时间已到，加入执行队列: ID={task.task_id}, 计划时间={task.schedule_time}"
                    )
                    task.status = TaskStatus.PENDING
                    await self.queue.put(task)

                    # 更新数据库中的任务状态
                    try:
                        async with AsyncSessionLocal() as db:
                            task_update = TaskUpdate(status=TaskStatus.PENDING)
                            await TaskService.update_task(db, task.task_id, task_update)
                    except Exception as e:
                        logger.error(f"更新任务状态失败: {e}")
            except Exception as e:
                logger.error(f"处理定时任务失败: {e}")

            # 每秒检查一次
            await asyncio.sleep(1)

    async def retry_task(self, task: Task):
        """重试任务"""
        task.retry_count += 1
        task.status = TaskStatus.RETRYING
        logger.info(
            f"重试任务: ID={task.task_id}, 重试次数={task.retry_count}/{task.max_retries}"
        )

        # 更新任务状态
        self.update_task_status(
            task.task_id,
            TaskStatus.RETRYING,
            0,
            error=f"任务失败，正在重试 ({task.retry_count}/{task.max_retries})",
        )

        # 如果已达到最大重试次数，则标记为失败
        if task.retry_count >= task.max_retries:
            logger.error(f"任务重试次数已达上限: ID={task.task_id}")
            task.status = TaskStatus.COMPLETED
            task.error = f"任务失败，已达到最大重试次数 ({task.max_retries})"

            # 发送失败通知
            await self._send_task_notification(
                task,
                f"{self._get_task_type_name(task.task_type)}任务重试失败",
                f"您的{self._get_task_type_name(task.task_type)}任务 (ID: {task.task_id}) 在重试 {task.max_retries} 次后仍然失败。请检查任务详情了解更多信息。",
                "failed",
            )

            # 更新数据库中的任务状态
            try:
                async with AsyncSessionLocal() as db:
                    task_update = TaskUpdate(
                        status=TaskStatus.COMPLETED,
                        error=task.error,
                        retry_count=task.retry_count,
                    )
                    await TaskService.update_task(db, task.task_id, task_update)
            except Exception as e:
                logger.error(f"更新任务状态失败: {e}")

            return

        # 等待一段时间后重试
        retry_delay = min(2**task.retry_count, 60)  # 指数退避，最大60秒
        logger.info(f"等待 {retry_delay} 秒后重试任务: ID={task.task_id}")
        await asyncio.sleep(retry_delay)

        # 重新加入队列
        await self.queue.put(task)
        logger.info(f"任务已重新加入队列: ID={task.task_id}")

        # 更新数据库中的任务状态
        try:
            async with AsyncSessionLocal() as db:
                task_update = TaskUpdate(
                    status=TaskStatus.RETRYING,
                    retry_count=task.retry_count,
                    error=f"任务失败，正在重试 ({task.retry_count}/{task.max_retries})",
                )
                await TaskService.update_task(db, task.task_id, task_update)
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")

    def _get_task_type_name(self, task_type: str) -> str:
        """获取任务类型的中文名称"""
        task_type_names = {
            "douyin_post": "抖音发布",
            "video_processing": "视频处理",
        }
        return task_type_names.get(task_type, "未知类型")

    async def process_tasks(self):
        """主任务处理循环"""
        logger.info("启动任务处理循环")

        # 确保已初始化
        if not self.initialized:
            await self.initialize()

        while True:
            logger.info("等待新任务...")
            task = await self.queue.get()
            logger.info(f"获取到新任务: ID={task.task_id}, 类型={task.task_type}")
            try:
                task.status = TaskStatus.RUNNING
                logger.info(f"开始处理任务: ID={task.task_id}")

                # 更新数据库中的任务状态
                try:
                    async with AsyncSessionLocal() as db:
                        task_update = TaskUpdate(status=TaskStatus.RUNNING)
                        await TaskService.update_task(db, task.task_id, task_update)
                except Exception as e:
                    logger.error(f"更新任务状态失败: {e}")

                if task.task_type == "douyin_post":
                    logger.info(f"处理抖音发布任务: ID={task.task_id}")
                    success = await self._process_douyin_post(task)
                    if not success and task.retry_count < task.max_retries:
                        logger.info(f"任务失败，准备重试: ID={task.task_id}")
                        await self.retry_task(task)
                        continue
                    else:
                        # 无论成功还是失败，任务都已完成
                        task.status = TaskStatus.COMPLETED
                        if not success:
                            logger.error(f"抖音发布任务失败: ID={task.task_id}")
                            task.error = "抖音发布任务失败"
                            # 发送失败通知
                            await self._send_task_notification(
                                task,
                                "抖音发布任务失败",
                                f"您的抖音发布任务 (ID: {task.task_id}) 执行失败。请检查任务详情了解更多信息。",
                                "failed",
                            )
                        else:
                            logger.info(f"抖音发布任务成功: ID={task.task_id}")
                            # 发送成功通知
                            await self._send_task_notification(
                                task,
                                "抖音发布任务完成",
                                f"您的抖音发布任务 (ID: {task.task_id}) 已成功完成。成功发布账号数: {task.result.get('success_count', 0)}，失败账号数: {len(task.result.get('failed_accounts', []))}。",
                                "success",
                            )
                elif task.task_type == "video_processing":
                    logger.info(f"处理视频任务: ID={task.task_id}")
                    await self._process_video(task)
                    # 视频处理任务的通知在_process_video方法中处理
                else:
                    logger.warning(f"未知任务类型: {task.task_type}")
                    task.status = TaskStatus.FAILED
                    task.error = f"未知任务类型: {task.task_type}"
                    # 发送失败通知
                    await self._send_task_notification(
                        task,
                        "未知任务类型",
                        f"您的任务 (ID: {task.task_id}) 因为未知的任务类型 {task.task_type} 而执行失败。",
                        "failed",
                    )

                # 更新数据库中的任务状态
                try:
                    async with AsyncSessionLocal() as db:
                        task_update = TaskUpdate(
                            status=task.status,
                            progress=task.progress,
                            result=task.result,
                            error=task.error,
                        )
                        await TaskService.update_task(db, task.task_id, task_update)
                except Exception as e:
                    logger.error(f"更新任务状态失败: {e}")

            except Exception as e:
                logger.exception(f"处理任务时出错: ID={task.task_id}, 错误={str(e)}")
                task.status = TaskStatus.FAILED
                task.error = f"处理任务时出错: {str(e)}"
                # 发送失败通知
                await self._send_task_notification(
                    task,
                    "任务执行出错",
                    f"您的任务 (ID: {task.task_id}) 执行过程中出现错误: {str(e)}。",
                    "failed",
                )

                # 更新数据库中的任务状态
                try:
                    async with AsyncSessionLocal() as db:
                        task_update = TaskUpdate(
                            status=TaskStatus.FAILED, error=task.error
                        )
                        await TaskService.update_task(db, task.task_id, task_update)
                except Exception as e:
                    logger.error(f"更新任务状态失败: {e}")
            finally:
                self.queue.task_done()
                logger.info(f"任务处理完成: ID={task.task_id}, 状态={task.status}")

    async def _process_douyin_post(self, task: Task) -> bool:
        """处理抖音视频发布任务"""
        accounts = task.data.get("accounts", [])
        video_info = task.data.get("video_info", {})
        user_id = task.data.get("user_id")
        total = len(accounts)
        success_count = 0
        failed_accounts = []

        try:
            for i, account in enumerate(accounts):
                try:
                    # 这里实现实际的抖音发布逻辑
                    logger.info(f"Posting video to account {account}")
                    await asyncio.sleep(2)  # 模拟发布耗时

                    # 模拟发布成功
                    success = True  # 实际需要根据API返回判断
                    if success:
                        success_count += 1
                    else:
                        failed_accounts.append(account)

                    progress = int((i + 1) / total * 100)
                    self.update_task_status(
                        task.task_id,
                        TaskStatus.RUNNING,
                        progress,
                        result={
                            "success_count": success_count,
                            "failed_accounts": failed_accounts,
                        },
                    )

                except Exception as e:
                    logger.error(f"Error posting to account {account}: {e}")
                    failed_accounts.append(account)

            # 更新任务状态和结果
            all_success = len(failed_accounts) == 0
            task.status = TaskStatus.COMPLETED if all_success else TaskStatus.FAILED
            task.progress = 100
            task.result = {
                "success_count": success_count,
                "failed_accounts": failed_accounts,
                "total_accounts": total,
            }

            return all_success

        except Exception as e:
            logger.error(f"Error in _process_douyin_post for task {task.task_id}: {e}")
            raise

    async def _process_video(self, task: Task) -> None:
        """处理视频AI任务"""
        try:
            logger.info(f"开始处理视频任务: ID={task.task_id}")
            self.update_task_status(task.task_id, TaskStatus.RUNNING, 10)

            # 获取任务参数
            original_path = task.data["original_path"]
            # 生成处理后的视频路径，而不是从任务数据中获取
            timestamp = int(datetime.now().timestamp())
            filename = os.path.basename(original_path)
            processed_filename = f"processed_{timestamp}_{filename}"
            processed_path = os.path.join(
                "uploads/processed_videos", processed_filename
            )

            # 确保目录存在
            os.makedirs("uploads/processed_videos", exist_ok=True)
            os.makedirs("uploads/temp", exist_ok=True)
            os.makedirs("uploads/voices", exist_ok=True)
            os.makedirs("static/previews", exist_ok=True)

            # 获取任务数据
            text = task.data["text"]
            remove_subtitles = task.data.get("remove_subtitles", True)
            generate_subtitles = task.data.get("generate_subtitles", False)
            selected_area = task.data.get("selected_area")
            auto_detect_subtitles = task.data.get("auto_detect", False)
            user_id = task.data.get("user_id")  # 获取用户ID
            subtitle_removal_mode = task.data.get("subtitle_removal_mode", "balanced")
            processing_mode = task.data.get("processing_mode", "cloud")

            # 获取新增的AI视频处理参数
            extract_voice = task.data.get("extract_voice", False)
            generate_speech = task.data.get("generate_speech", False)
            lip_sync = task.data.get("lip_sync", False)
            add_subtitles = task.data.get("add_subtitles", False)
            voice_text = task.data.get("voice_text", "")
            processing_pipeline = task.data.get("processing_pipeline", [])
            subtitle_style = task.data.get("subtitle_style", {})

            logger.info(
                f"视频任务参数: 原始路径={original_path}, 处理路径={processed_path}, "
                f"文本={text}, 移除字幕={remove_subtitles}, 生成字幕={generate_subtitles}, "
                f"字幕移除模式={subtitle_removal_mode}, 处理模式={processing_mode}, "
                f"提取音色={extract_voice}, 生成语音={generate_speech}, 唇形同步={lip_sync}, "
                f"添加字幕={add_subtitles}, 处理流程={processing_pipeline}"
            )

            # 根据处理流程选择不同的处理方式
            if processing_pipeline and any(
                [extract_voice, generate_speech, lip_sync, add_subtitles]
            ):
                # 使用新的VideoProcessingService处理
                from app.core.video_processing_service import VideoProcessingService

                # 创建视频处理服务实例
                video_service = VideoProcessingService(
                    base_dir="uploads",
                    temp_dir="uploads/temp",
                    output_dir="uploads/processed_videos",
                    voice_dir="uploads/voices",
                )

                # 定义进度回调函数
                async def progress_callback(
                    task_id: str, progress: int, message: str, data: Dict[str, Any]
                ):
                    logger.info(
                        f"视频处理进度: ID={task_id}, 进度={progress}%, 消息={message}"
                    )

                    # 从数据中提取当前处理阶段
                    current_stage = data.get("current_stage")

                    self.update_task_status(
                        task_id,
                        TaskStatus.RUNNING,
                        progress,
                        message=message,
                        current_stage=current_stage,
                    )

                # 如果需要添加字幕但没有在处理流程中，添加到处理流程
                if add_subtitles and "add_subtitles" not in processing_pipeline:
                    processing_pipeline.append("add_subtitles")
                    task.data["processing_pipeline"] = processing_pipeline

                # 执行视频处理
                logger.info(
                    f"开始执行高级视频处理: ID={task.task_id}, 处理流程={processing_pipeline}"
                )
                result = await video_service.process_video(
                    task_id=task.task_id,
                    task_data=task.data,
                    progress_callback=progress_callback,
                )

                if result["status"] == "completed":
                    # 处理成功
                    processed_path = result["output_path"]
                    thumbnail_path = result.get("preview_path", "")

                    # 如果没有生成预览图，尝试生成
                    if not thumbnail_path:
                        thumbnail_filename = f"thumbnail_{os.path.basename(processed_path).replace('.mp4', '.jpg')}"
                        thumbnail_path = os.path.join(
                            "static/previews", thumbnail_filename
                        )

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
                            logger.info(f"缩略图生成成功: {thumbnail_path}")
                        except Exception as e:
                            logger.error(f"生成缩略图失败: {str(e)}")
                            # 如果缩略图生成失败，使用默认缩略图
                            thumbnail_path = "static/default_preview.jpg"

                    # 生成视频URL和缩略图URL
                    video_filename = os.path.basename(processed_path)
                    video_url = f"/api/v1/douyin/processed-video/{task.task_id}"
                    thumbnail_url = (
                        f"/api/v1/douyin/processed-video-thumbnail/{task.task_id}"
                    )

                    task_result = {
                        "processed_path": processed_path,
                        "thumbnail_path": thumbnail_path,
                        "removed_subtitles": remove_subtitles,
                        "generated_subtitles": generate_subtitles,
                        "selected_area": selected_area,
                        "video_url": video_url,
                        "thumbnail_url": thumbnail_url,
                        "filename": video_filename,
                        "processing_pipeline": processing_pipeline,
                        "processing_time": result.get("processing_time", 0),
                    }

                    self.update_task_status(
                        task.task_id,
                        TaskStatus.COMPLETED,
                        100,
                        result=task_result,
                    )

                    # 发送成功通知
                    await self._send_task_notification(
                        task,
                        "视频处理完成",
                        f"您的视频已成功处理完成，处理流程: {', '.join(processing_pipeline)}。",
                        "success",
                        {
                            "video_url": video_url,
                            "thumbnail_url": thumbnail_url,
                        },
                    )

                    logger.info(f"高级视频处理成功完成: ID={task.task_id}")
                else:
                    # 处理失败
                    error_message = result.get("error", "未知错误")
                    self.update_task_status(
                        task.task_id,
                        TaskStatus.FAILED,
                        0,
                        error=f"视频处理失败: {error_message}",
                    )

                    # 发送失败通知
                    await self._send_task_notification(
                        task,
                        "视频处理失败",
                        f"您的视频处理失败: {error_message}",
                        "error",
                    )

                    logger.error(
                        f"高级视频处理失败: ID={task.task_id}, 错误={error_message}"
                    )
            else:
                # 使用原有的VideoProcessor处理（仅字幕擦除功能）
                # 创建视频处理器实例
                from app.core.ai_services import VideoProcessor

                processor = VideoProcessor()
                logger.info(f"已创建视频处理器: ID={task.task_id}")

                # 定义进度回调函数
                def progress_callback(progress: float):
                    logger.info(
                        f"视频处理进度: ID={task.task_id}, 进度={int(progress)}%"
                    )
                    self.update_task_status(
                        task.task_id, TaskStatus.RUNNING, int(progress)
                    )

                # 处理选项
                options = {
                    "output_path": processed_path,
                    "remove_subtitles": remove_subtitles,
                    "generate_subtitles": generate_subtitles,
                    "selected_area": selected_area,
                    "auto_detect_subtitles": auto_detect_subtitles,
                    "language": "chinese",  # 默认使用中文
                    "subtitle_removal_mode": subtitle_removal_mode,  # 添加字幕移除模式
                    "processing_mode": processing_mode,  # 添加处理模式
                }

                # 执行视频处理
                logger.info(f"开始执行视频处理: ID={task.task_id}")
                success = await processor.process_video(
                    original_path, text, options, progress_callback
                )
                logger.info(f"视频处理完成: ID={task.task_id}, 成功={success}")

                # 无论成功还是失败，任务状态都是已完成
                task.status = TaskStatus.COMPLETED

                if success:
                    # 生成缩略图
                    thumbnail_filename = f"thumbnail_{os.path.basename(processed_path).replace('.mp4', '.jpg')}"
                    thumbnail_path = os.path.join("static/previews", thumbnail_filename)

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
                        logger.info(f"缩略图生成成功: {thumbnail_path}")
                    except Exception as e:
                        logger.error(f"生成缩略图失败: {str(e)}")
                        # 如果缩略图生成失败，使用默认缩略图
                        thumbnail_path = "static/default_preview.jpg"

                    # 生成视频URL和缩略图URL
                    video_filename = os.path.basename(processed_path)
                    video_url = f"/api/v1/douyin/processed-video/{task.task_id}"
                    thumbnail_url = (
                        f"/api/v1/douyin/processed-video-thumbnail/{task.task_id}"
                    )
                    logger.info(f"生成视频URL: ID={task.task_id}, URL={video_url}")

                    result = {
                        "processed_path": processed_path,
                        "thumbnail_path": thumbnail_path,
                        "removed_subtitles": remove_subtitles,
                        "generated_subtitles": generate_subtitles,
                        "selected_area": selected_area,
                        "video_url": video_url,
                        "thumbnail_url": thumbnail_url,
                        "filename": video_filename,
                    }

                    self.update_task_status(
                        task.task_id,
                        TaskStatus.COMPLETED,
                        100,
                        result=result,
                    )

                    # 发送成功通知
                    await self._send_task_notification(
                        task,
                        "视频处理完成",
                        "您的视频已成功处理完成。",
                        "success",
                        {
                            "video_url": video_url,
                            "thumbnail_url": thumbnail_url,
                        },
                    )

                    logger.info(f"视频处理成功完成: ID={task.task_id}")
                else:
                    # 处理失败
                    self.update_task_status(
                        task.task_id,
                        TaskStatus.FAILED,
                        0,
                        error="视频处理失败",
                    )

                    # 发送失败通知
                    await self._send_task_notification(
                        task,
                        "视频处理失败",
                        "您的视频处理失败，请重试或联系管理员。",
                        "error",
                    )

                    logger.error(f"视频处理失败: ID={task.task_id}")

        except Exception as e:
            logger.exception(f"处理视频任务时出错: ID={task.task_id}, 错误={str(e)}")
            self.update_task_status(
                task.task_id,
                TaskStatus.FAILED,
                0,
                error=f"处理视频任务时出错: {str(e)}",
            )

            # 发送失败通知
            await self._send_task_notification(
                task,
                "视频处理出错",
                f"您的视频处理过程中出现错误: {str(e)}",
                "error",
            )

    async def _send_task_notification(
        self, task: Task, title: str, message: str, status: str
    ):
        """发送任务通知"""
        try:
            # 获取用户ID
            user_id = task.data.get("user_id")
            if not user_id:
                logger.warning(f"任务 {task.task_id} 没有关联用户ID，无法发送通知")
                return

            # 创建异步数据库会话
            async with AsyncSessionLocal() as async_db:
                # 根据任务类型设置不同的任务类型标识
                task_type = (
                    "video_processing"
                    if task.task_type == "video_processing"
                    else "douyin_post"
                )

                # 创建通知
                await NotificationService.create_task_notification(
                    db=async_db,
                    user_id=user_id,
                    title=title,
                    content=message,
                    task_id=task.task_id,
                    task_type=task_type,
                )

                logger.info(
                    f"已发送通知: 用户={user_id}, 标题={title}, 任务ID={task.task_id}"
                )
        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}")
