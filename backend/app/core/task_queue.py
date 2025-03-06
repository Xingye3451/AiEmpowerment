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
        return cls._instance

    async def add_task(self, task: Task) -> str:
        logger.info(f"添加任务到队列: ID={task.task_id}, 类型={task.task_type}")
        self.tasks[task.task_id] = task

        if task.schedule_time and task.schedule_time > datetime.now():
            # 如果是定时任务且时间未到，加入定时队列
            task.status = TaskStatus.SCHEDULED
            logger.info(f"任务 {task.task_id} 已调度，将在 {task.schedule_time} 执行")
            heapq.heappush(
                self.scheduled_tasks, ScheduledTask(task.schedule_time, task)
            )
        else:
            # 否则直接加入普通队列
            logger.info(f"任务 {task.task_id} 已加入执行队列")
            await self.queue.put(task)

        if not self.running:
            logger.info("启动任务处理循环")
            self.running = True
            asyncio.create_task(self._process_queue())

        logger.info(f"任务添加完成: ID={task.task_id}")
        return task.task_id

    async def _process_queue(self):
        """
        任务处理队列的入口点
        这是 process_tasks 方法的别名，为了向后兼容
        """
        await self.process_tasks()

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    def update_task_status(
        self,
        task_id: str,
        status: str = None,
        progress: int = None,
        result: dict = None,
        error: str = None,
        **kwargs,
    ):
        """更新任务状态"""
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

        if result:
            task.result = result

        if error:
            task.error = error
            logger.error(f"任务错误: ID={task_id}, 错误={error}")

        for key, value in kwargs.items():
            setattr(task, key, value)

        task.updated_at = datetime.now()

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

                logger.info(f"Cleaned up {len(old_tasks)} old tasks")
            except Exception as e:
                logger.error(f"Error cleaning up old tasks: {e}")

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
                    logger.info(
                        f"Processing scheduled task {scheduled_task.task.task_id}"
                    )
                    await self.queue.put(scheduled_task.task)
                    scheduled_task.task.status = TaskStatus.PENDING

                # 检查失败的任务是否需要重试
                for task in self.tasks.values():
                    if (
                        task.status == TaskStatus.FAILED
                        and task.retry_count < task.max_retries
                    ):
                        if task.last_retry:
                            delay = self.retry_delays[
                                min(task.retry_count, len(self.retry_delays) - 1)
                            ]
                            if (now - task.last_retry).total_seconds() >= delay:
                                await self.retry_task(task)

            except Exception as e:
                logger.error(f"Error in process_scheduled_tasks: {e}")

            await asyncio.sleep(1)  # 每秒检查一次

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
            return

        # 等待一段时间后重试
        retry_delay = min(2**task.retry_count, 60)  # 指数退避，最大60秒
        logger.info(f"等待 {retry_delay} 秒后重试任务: ID={task.task_id}")
        await asyncio.sleep(retry_delay)

        # 重新加入队列
        await self.queue.put(task)
        logger.info(f"任务已重新加入队列: ID={task.task_id}")

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
        # 启动定时任务处理器和清理任务
        asyncio.create_task(self.process_scheduled_tasks())
        asyncio.create_task(self.cleanup_old_tasks())

        while True:
            logger.info("等待新任务...")
            task = await self.queue.get()
            logger.info(f"获取到新任务: ID={task.task_id}, 类型={task.task_type}")
            try:
                task.status = TaskStatus.RUNNING
                logger.info(f"开始处理任务: ID={task.task_id}")

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
            processed_path = task.data["processed_path"]
            text = task.data["text"]
            remove_subtitles = task.data.get("remove_subtitles", True)
            generate_subtitles = task.data.get("generate_subtitles", False)
            selected_area = task.data.get("selected_area")
            auto_detect_subtitles = task.data.get("auto_detect_subtitles", False)
            user_id = task.data.get("user_id")  # 获取用户ID

            logger.info(
                f"视频任务参数: 原始路径={original_path}, 处理路径={processed_path}, 文本={text}, 移除字幕={remove_subtitles}, 生成字幕={generate_subtitles}"
            )

            # 创建视频处理器实例
            processor = VideoProcessor()
            logger.info(f"已创建视频处理器: ID={task.task_id}")

            # 定义进度回调函数
            def progress_callback(progress: float):
                logger.info(f"视频处理进度: ID={task.task_id}, 进度={int(progress)}%")
                self.update_task_status(task.task_id, TaskStatus.RUNNING, int(progress))

            # 处理选项
            options = {
                "output_path": processed_path,
                "remove_subtitles": remove_subtitles,
                "generate_subtitles": generate_subtitles,
                "selected_area": selected_area,
                "auto_detect_subtitles": auto_detect_subtitles,
                "language": "chinese",  # 默认使用中文
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
                # 生成视频URL和缩略图URL
                video_filename = os.path.basename(processed_path)
                video_url = f"/api/v1/douyin/processed-video/{task.task_id}"
                thumbnail_url = (
                    f"/api/v1/douyin/processed-video-thumbnail/{task.task_id}"
                )
                logger.info(f"生成视频URL: ID={task.task_id}, URL={video_url}")

                result = {
                    "processed_path": processed_path,
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
                logger.info(f"任务状态已更新为已完成: ID={task.task_id}")

                # 发送成功通知
                await self._send_task_notification(
                    task,
                    "视频处理完成",
                    f"您的视频处理任务 (ID: {task.task_id}) 已成功完成。您可以在任务详情中查看和下载处理后的视频。",
                    "success",
                )
            else:
                # 处理失败，但任务状态仍然是已完成
                logger.error(f"视频处理失败: ID={task.task_id}")
                self.update_task_status(
                    task.task_id, TaskStatus.COMPLETED, 100, error="视频处理失败"
                )
                logger.info(f"任务状态已更新为已完成（失败）: ID={task.task_id}")

                # 发送失败通知
                await self._send_task_notification(
                    task,
                    "视频处理失败",
                    f"您的视频处理任务 (ID: {task.task_id}) 执行失败。请检查任务详情了解更多信息。",
                    "failed",
                )
        except Exception as e:
            logger.exception(f"视频处理出错: ID={task.task_id}, 错误={str(e)}")
            self.update_task_status(
                task.task_id, TaskStatus.COMPLETED, 100, error=f"视频处理出错: {str(e)}"
            )

            # 发送错误通知
            await self._send_task_notification(
                task,
                "视频处理出错",
                f"您的视频处理任务 (ID: {task.task_id}) 执行过程中出现错误: {str(e)}。",
                "failed",
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
