import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import threading
import time
import uuid
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.scheduled_task import ScheduledTask
from app.models.content_collection import CollectionTask
from app.utils.douyin_crawler import DouyinCrawler
from app.utils.kuaishou_crawler import KuaishouCrawler
from app.utils.bilibili_crawler import BiliBiliCrawler
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class Scheduler:
    """定时任务调度器"""

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.thread = None

    def start(self):
        """启动调度器"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("调度器已启动")

    def stop(self):
        """停止调度器"""
        if not self.running:
            logger.info("调度器已经停止，无需再次停止")
            return

        logger.info("正在停止调度器...")
        self.running = False

        if self.thread and self.thread.is_alive():
            logger.info("正在等待调度器线程退出...")
            # 在Linux容器环境中，可能需要更短的超时时间
            self.thread.join(timeout=1.5)

            if self.thread.is_alive():
                logger.warning("调度器线程未能在规定时间内退出，强制结束")
                # 在Linux环境中，我们不能直接终止线程，但可以标记它为daemon
                # 这样在主程序退出时，它会自动终止
                self.thread = None
            else:
                logger.info("调度器线程已成功退出")
                self.thread = None
        else:
            logger.info("调度器没有活动的线程")

        logger.info("调度器已停止")

    def _run_scheduler(self):
        """运行调度器主循环"""
        while self.running:
            try:
                # 检查是否有任务需要执行
                now = datetime.now()
                tasks_to_run = []

                for task_id, task_info in list(self.tasks.items()):
                    if task_info["status"] == "active" and task_info["next_run"] <= now:
                        tasks_to_run.append((task_id, task_info))

                # 执行需要运行的任务
                for task_id, task_info in tasks_to_run:
                    self._execute_task(task_id, task_info)

                # 每10秒检查一次
                time.sleep(10)

            except Exception as e:
                logger.error(f"调度器运行错误: {str(e)}")
                time.sleep(30)  # 出错后等待30秒再继续

    def _execute_task(self, task_id: str, task_info: Dict[str, Any]):
        """执行任务"""
        try:
            logger.info(f"执行任务: {task_id} - {task_info['name']}")

            # 创建数据库会话
            db = SessionLocal()

            try:
                # 更新任务状态
                task = (
                    db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                )
                if task:
                    task.last_run = datetime.now()

                    # 根据任务类型执行不同的操作
                    if task.type == "content_collection":
                        self._execute_collection_task(db, task)
                    elif task.type == "content_distribution":
                        self._execute_distribution_task(db, task)
                    elif task.type == "data_analysis":
                        self._execute_analysis_task(db, task)

                    # 计算下一次执行时间
                    task.next_run = self._calculate_next_run(task.schedule)

                    # 更新任务信息
                    db.add(task)
                    db.commit()

                    # 更新内存中的任务信息
                    self.tasks[task_id]["next_run"] = task.next_run

                    # 发送任务执行完成通知
                    NotificationService.create_scheduled_task_notification(
                        db=db,
                        user_id=task.user_id,
                        title=f"定时任务已执行: {task.name}",
                        content=f"您的定时任务 {task.name} 已于 {task.last_run.strftime('%Y-%m-%d %H:%M:%S')} 执行完成。",
                        task_id=task.id,
                    )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"执行任务 {task_id} 失败: {str(e)}")

    def _execute_collection_task(self, db: Session, task: ScheduledTask):
        """执行内容采集任务"""
        # 获取任务数据
        data = task.data
        if not data:
            logger.error(f"任务 {task.id} 没有数据")
            return

        # 创建采集任务
        collection_task = CollectionTask(
            name=f"定时采集: {data.get('query', '未知查询')}",
            query=data.get("query"),
            platforms=data.get("platforms", ["douyin"]),
            filters=data.get("filters", {}),
            user_id=task.user_id,
            scheduled_task_id=task.id,
            status="running",
        )

        db.add(collection_task)
        db.commit()
        db.refresh(collection_task)

        # 启动异步任务执行采集
        asyncio.run(self._run_collection_task(db, collection_task))

    async def _run_collection_task(self, db: Session, collection_task: CollectionTask):
        """运行采集任务"""
        try:
            # 获取任务数据
            query = collection_task.query
            platforms = collection_task.platforms
            filters = collection_task.filters or {}

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

                    total_found += len(videos)

                    # 保存视频数据
                    # 这里省略具体的保存逻辑，与content_collection.py中的逻辑类似

                except Exception as e:
                    logger.error(f"平台 {platform} 搜索失败: {str(e)}")

            # 更新任务状态
            collection_task.status = "completed"
            collection_task.total_found = total_found
            collection_task.completed_at = datetime.now()
            db.add(collection_task)
            db.commit()

            # 发送任务完成通知
            NotificationService.create_task_notification(
                db=db,
                user_id=collection_task.user_id,
                title=f"内容采集任务已完成: {collection_task.name}",
                content=f"您的内容采集任务 {collection_task.name} 已完成，共采集到 {total_found} 条内容。",
                task_id=collection_task.id,
                task_type="collection_task",
            )

        except Exception as e:
            logger.error(f"执行采集任务 {collection_task.id} 失败: {str(e)}")
            collection_task.status = "failed"
            db.add(collection_task)
            db.commit()

            # 发送任务失败通知
            NotificationService.create_task_notification(
                db=db,
                user_id=collection_task.user_id,
                title=f"内容采集任务失败: {collection_task.name}",
                content=f"您的内容采集任务 {collection_task.name} 执行失败，请检查任务配置。",
                task_id=collection_task.id,
                task_type="collection_task",
            )

    def _execute_distribution_task(self, db: Session, task: ScheduledTask):
        """执行内容分发任务"""
        # 这里实现内容分发的逻辑
        logger.info(f"执行内容分发任务: {task.id}")

    def _execute_analysis_task(self, db: Session, task: ScheduledTask):
        """执行数据分析任务"""
        # 这里实现数据分析的逻辑
        logger.info(f"执行数据分析任务: {task.id}")

    def _calculate_next_run(self, schedule: Dict[str, Any]) -> datetime:
        """计算下次执行时间"""
        now = datetime.now()
        schedule_type = schedule.get("type", "once")
        time_parts = schedule.get("time", "00:00:00").split(":")
        hours, minutes, seconds = (
            int(time_parts[0]),
            int(time_parts[1]),
            int(time_parts[2]),
        )

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

    def add_task(self, task: ScheduledTask):
        """添加任务到调度器"""
        self.tasks[task.id] = {
            "id": task.id,
            "name": task.name,
            "type": task.type,
            "status": task.status,
            "schedule": task.schedule,
            "data": task.data,
            "next_run": task.next_run or datetime.now(),
            "user_id": task.user_id,
        }
        logger.info(f"添加任务: {task.id} - {task.name}")

    def update_task(self, task: ScheduledTask):
        """更新任务"""
        if task.id in self.tasks:
            self.tasks[task.id] = {
                "id": task.id,
                "name": task.name,
                "type": task.type,
                "status": task.status,
                "schedule": task.schedule,
                "data": task.data,
                "next_run": task.next_run or datetime.now(),
                "user_id": task.user_id,
            }
            logger.info(f"更新任务: {task.id} - {task.name}")

    def remove_task(self, task_id: str):
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"移除任务: {task_id}")

    def load_tasks(self):
        """从数据库加载所有活动任务"""
        try:
            db = SessionLocal()
            try:
                tasks = (
                    db.query(ScheduledTask)
                    .filter(ScheduledTask.status == "active")
                    .all()
                )
                for task in tasks:
                    self.add_task(task)

                logger.info(f"已加载 {len(tasks)} 个活动任务")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"加载任务失败: {str(e)}")


# 创建全局调度器实例
scheduler = Scheduler()


# 应用启动时初始化调度器
def init_scheduler():
    scheduler.load_tasks()
    scheduler.start()


# 应用关闭时停止调度器
def shutdown_scheduler():
    scheduler.stop()
