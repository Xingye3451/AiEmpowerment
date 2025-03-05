# 导入所有模型，以便在初始化数据库时使用
from app.db.base_class import Base
from app.models.user import User
from app.models.social_account import (
    SocialAccount,
    AccountGroup,
    SocialPost,
    DistributionTask,
)
from app.models.notification import Notification
from app.models.scheduled_task import ScheduledTask
from app.models.comfyui import ComfyUIWorkflow
from app.models.content_collection import (
    CollectedVideo,
    CollectionTask,
    CollectedContent,
    ContentTag,
)
