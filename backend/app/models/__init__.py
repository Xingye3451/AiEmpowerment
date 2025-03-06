# 导入所有模型，确保在初始化数据库时能够正确创建所有表

from app.models.user import User
from app.models.task import Task
from app.models.social_account import (
    SocialAccount,
    AccountGroup,
    SocialPost,
    DistributionTask,
    account_group_association,
)
from app.models.notification import Notification
from app.models.comfyui import ComfyUIWorkflow
from app.models.scheduled_task import ScheduledTask
from app.models.content_collection import (
    CollectionTask,
    CollectedContent,
    CollectedVideo,
)

# 导出所有模型
__all__ = [
    "User",
    "Task",
    "SocialAccount",
    "AccountGroup",
    "SocialPost",
    "DistributionTask",
    "Notification",
    "ComfyUIWorkflow",
    "ScheduledTask",
    "CollectionTask",
    "CollectedContent",
    "CollectedVideo",
]
