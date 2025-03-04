from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import heapq
from dataclasses import dataclass, field
import logging
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User
from app.core.config import settings
import os
import subprocess
import shutil

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
        self.tasks[task.task_id] = task

        if task.schedule_time and task.schedule_time > datetime.now():
            # 如果是定时任务且时间未到，加入定时队列
            task.status = TaskStatus.SCHEDULED
            heapq.heappush(
                self.scheduled_tasks, ScheduledTask(task.schedule_time, task)
            )
        else:
            # 否则直接加入普通队列
            await self.queue.put(task)

        if not self.running:
            self.running = True
            asyncio.create_task(self._process_queue())

        return task.task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: int = None,
        result: dict = None,
        error: str = None,
    ):
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            if progress is not None:
                task.progress = progress
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
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

    async def update_history(self, task: Task):
        """更新用户的任务历史记录"""
        try:
            db = SessionLocal()
            try:
                user = (
                    db.query(User).filter(User.id == task.data.get("user_id")).first()
                )
                if user and user.douyin_history is not None:
                    for record in user.douyin_history:
                        if record.get("task_id") == task.task_id:
                            record.update(
                                {
                                    "status": task.status,
                                    "success_count": (
                                        task.result.get("success_count", 0)
                                        if task.result
                                        else 0
                                    ),
                                    "failed_count": (
                                        len(task.result.get("failed_accounts", []))
                                        if task.result
                                        else 0
                                    ),
                                    "updated_at": task.updated_at.isoformat(),
                                    "retries": task.retry_count,
                                }
                            )
                            break
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error updating history for task {task.task_id}: {e}")

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
        """重试失败的任务"""
        if task.retry_count >= task.max_retries:
            task.status = TaskStatus.FAILED
            task.error = f"达到最大重试次数 ({task.max_retries})"
            await self.update_history(task)
            return

        delay = self.retry_delays[min(task.retry_count, len(self.retry_delays) - 1)]
        task.retry_count += 1
        task.status = TaskStatus.RETRYING
        task.last_retry = datetime.now()

        logger.info(
            f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})"
        )
        await self.update_history(task)

        # 等待指定时间后重试
        await asyncio.sleep(delay)
        await self.queue.put(task)

    async def process_tasks(self):
        """主任务处理循环"""
        # 启动定时任务处理器和清理任务
        asyncio.create_task(self.process_scheduled_tasks())
        asyncio.create_task(self.cleanup_old_tasks())

        while True:
            task = await self.queue.get()
            try:
                task.status = TaskStatus.RUNNING
                await self.update_history(task)

                if task.task_type == "douyin_post":
                    success = await self._process_douyin_post(task)
                    if not success and task.retry_count < task.max_retries:
                        await self.retry_task(task)
                        continue
                elif task.task_type == "video_processing":
                    await self._process_video(task)

            except Exception as e:
                logger.error(f"Error processing task {task.task_id}: {e}")
                task.error = str(e)
                if task.retry_count < task.max_retries:
                    await self.retry_task(task)
                else:
                    task.status = TaskStatus.FAILED
                    await self.update_history(task)
            finally:
                task.updated_at = datetime.now()
                await self.update_history(task)
                self.queue.task_done()

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
                    await self.update_history(task)

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
            self.update_task_status(task.task_id, TaskStatus.RUNNING, 10)

            original_path = task.data["original_path"]
            processed_path = task.data["processed_path"]
            text = task.data["text"]
            remove_subtitles = task.data.get("remove_subtitles", True)
            generate_subtitles = task.data.get("generate_subtitles", False)
            selected_area = task.data.get("selected_area")
            auto_detect_subtitles = task.data.get("auto_detect_subtitles", False)

            current_video_path = original_path
            progress = 10

            # 1. 如果需要，使用AI模型去除字幕并修复背景
            if remove_subtitles:
                no_subtitle_path = (
                    f"{os.path.splitext(original_path)[0]}_no_subtitle.mp4"
                )
                try:
                    from app.core.ai_services import RunwayMLService

                    runway_service = RunwayMLService()
                    await runway_service.inpaint_video(
                        input_path=current_video_path,
                        output_path=no_subtitle_path,
                        mask_type="text",  # 指定要移除文字
                        restoration_quality="high",
                        selected_area=selected_area,
                        auto_detect=auto_detect_subtitles,  # 添加自动检测选项
                    )
                    current_video_path = no_subtitle_path
                    progress = 40
                    self.update_task_status(task.task_id, TaskStatus.RUNNING, progress)
                except Exception as e:
                    raise Exception(f"AI移除字幕失败: {str(e)}")

            # 2. 使用MockingBird或YourTTS进行声音克隆
            try:
                from app.core.ai_services import VoiceCloningService

                voice_service = VoiceCloningService()
                # 提取原始音频中的声音特征
                voice_features = await voice_service.extract_voice_features(
                    original_path
                )
                # 使用提取的声音特征生成新的语音
                new_audio_path = f"{os.path.splitext(original_path)[0]}_new_audio.wav"
                await voice_service.generate_speech(
                    text=text, voice_features=voice_features, output_path=new_audio_path
                )
                progress = 70
                self.update_task_status(task.task_id, TaskStatus.RUNNING, progress)
            except Exception as e:
                raise Exception(f"AI语音克隆失败: {str(e)}")

            # 3. 使用Wav2Lip或SadTalker进行唇形同步
            try:
                from app.core.ai_services import LipSyncService

                lip_sync_service = LipSyncService()
                temp_output_path = f"{os.path.splitext(processed_path)[0]}_temp.mp4"
                await lip_sync_service.sync_video_with_audio(
                    video_path=current_video_path,
                    audio_path=new_audio_path,
                    output_path=temp_output_path,
                    sync_quality="high",
                )
                current_video_path = temp_output_path
                progress = 90
                self.update_task_status(task.task_id, TaskStatus.RUNNING, progress)
            except Exception as e:
                raise Exception(f"AI口型同步失败: {str(e)}")

            # 4. 如果需要，生成新的字幕
            if generate_subtitles:
                try:
                    from app.core.ai_services import SubtitleService

                    subtitle_service = SubtitleService()
                    await subtitle_service.generate_subtitles(
                        video_path=current_video_path,
                        text=text,
                        output_path=processed_path,
                    )
                except Exception as e:
                    raise Exception(f"生成字幕失败: {str(e)}")
            else:
                # 如果不需要生成字幕，直接将当前处理的视频移动到最终位置
                shutil.move(current_video_path, processed_path)

            # 5. 清理临时文件
            temp_files = [
                f"{os.path.splitext(original_path)[0]}_no_subtitle.mp4",
                f"{os.path.splitext(original_path)[0]}_new_audio.wav",
                f"{os.path.splitext(processed_path)[0]}_temp.mp4",
            ]
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            self.update_task_status(
                task.task_id,
                TaskStatus.COMPLETED,
                100,
                result={
                    "processed_path": processed_path,
                    "removed_subtitles": remove_subtitles,
                    "generated_subtitles": generate_subtitles,
                    "selected_area": selected_area,
                },
            )

        except Exception as e:
            logger.error(f"处理视频失败: {str(e)}")
            self.update_task_status(task.task_id, TaskStatus.FAILED, 100, error=str(e))
