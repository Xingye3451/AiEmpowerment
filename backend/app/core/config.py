from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any, Union, ClassVar
import os
from functools import lru_cache
import yaml
import logging
import secrets
from pydantic import AnyHttpUrl, PostgresDsn

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # 配置文件路径
    config_file: str = os.getenv("CONFIG_FILE", "config/default.yaml")

    # 基础配置
    PROJECT_NAME: str = "AI赋能平台"
    PROJECT_DESCRIPTION: str = "AI赋能内容分发平台"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    ADMIN_TOKEN_EXPIRE_MINUTES: int = 60  # 管理员token默认有效期1小时
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # 数据库配置
    DB_TYPE: str = "sqlite"  # 默认使用SQLite

    # SQLite配置
    DB_FILE: str = "app.db"

    # MySQL配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DB: str = "aiempowerment"
    MYSQL_CHARSET: str = "utf8mb4"

    # 数据库URL（会根据DB_TYPE自动生成）
    DATABASE_URL: str = "sqlite:///./app.db"
    SYNC_DATABASE_URL: str = ""

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    PREVIEW_DIR: str = "static/previews"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    RESULT_DIR: str = "static/results"
    TEMP_DIR: str = "temp"
    STATIC_DIR: str = "static"

    # 抖音相关配置
    DOUYIN_API_TIMEOUT: int = 30
    MAX_RETRY_COUNT: int = 3
    RETRY_DELAY: List[int] = [60, 300, 900]  # 重试延迟：1分钟、5分钟、15分钟

    # AI服务API配置
    RUNWAY_API_KEY: str = os.getenv("RUNWAY_API_KEY", "")
    COQUI_API_KEY: str = ""
    SADTALKER_API_KEY: str = ""

    # 云服务API密钥
    ELEVEN_LABS_API_KEY: str = os.getenv("ELEVEN_LABS_API_KEY", "")
    SYNC_LABS_API_KEY: str = os.getenv("SYNC_LABS_API_KEY", "")
    REPLICATE_API_KEY: str = os.getenv("REPLICATE_API_KEY", "")

    # ComfyUI配置
    COMFYUI_URL: str = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")

    # 任务队列配置
    QUEUE_SIZE: int = 5

    # AI服务配置
    DEFAULT_SUBTITLE_REMOVAL_URL: str = os.getenv(
        "SUBTITLE_REMOVAL_URL", "http://subtitle-removal-service:8001"
    )
    DEFAULT_VOICE_SYNTHESIS_URL: str = os.getenv(
        "VOICE_SYNTHESIS_URL", "http://voice-synthesis-service:8002"
    )
    DEFAULT_LIP_SYNC_URL: str = os.getenv(
        "LIP_SYNC_URL", "http://lip-sync-service:8003"
    )

    # 视频增强配置
    VIDEO_ENHANCEMENT_CONFIG: Dict[str, Any] = {
        "service_type": "video_enhancement",
        "service_url": os.getenv("REALESRGAN_SERVICE_URL", "http://realesrgan:5003"),
        "default_mode": "standard",
        "timeout": 600,
        "model_type": "realesrgan-x4plus",
        "scale": 2,
        "denoise_strength": 0.5,
        "advanced_params": {},
    }

    # 更新默认配置
    DEFAULT_CONFIGS: Dict[str, Dict[str, Any]] = {
        # ... existing configs ...
        "video_enhancement": VIDEO_ENHANCEMENT_CONFIG,
    }

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_yaml_config()
        self.update_db_urls()

    def load_yaml_config(self):
        """从YAML文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                    # 更新配置
                    if config.get("project"):
                        self.PROJECT_NAME = config["project"].get(
                            "name", self.PROJECT_NAME
                        )
                        self.PROJECT_DESCRIPTION = config["project"].get(
                            "description", self.PROJECT_DESCRIPTION
                        )
                        self.PROJECT_VERSION = config["project"].get(
                            "version", self.PROJECT_VERSION
                        )
                        self.API_V1_STR = config["project"].get(
                            "api_prefix", self.API_V1_STR
                        )

                    if config.get("security"):
                        self.SECRET_KEY = config["security"].get(
                            "secret_key", self.SECRET_KEY
                        )
                        self.ALGORITHM = config["security"].get(
                            "algorithm", self.ALGORITHM
                        )
                        self.ACCESS_TOKEN_EXPIRE_MINUTES = config["security"].get(
                            "access_token_expire_minutes",
                            self.ACCESS_TOKEN_EXPIRE_MINUTES,
                        )
                        self.ADMIN_TOKEN_EXPIRE_MINUTES = config["security"].get(
                            "admin_token_expire_minutes",
                            self.ADMIN_TOKEN_EXPIRE_MINUTES,
                        )

                    if config.get("database"):
                        # 数据库类型
                        self.DB_TYPE = config["database"].get("type", self.DB_TYPE)

                        # SQLite配置
                        if config["database"].get("sqlite"):
                            self.DB_FILE = config["database"]["sqlite"].get(
                                "file", self.DB_FILE
                            )

                        # MySQL配置
                        if config["database"].get("mysql"):
                            mysql_config = config["database"]["mysql"]
                            self.MYSQL_HOST = mysql_config.get("host", self.MYSQL_HOST)
                            self.MYSQL_PORT = mysql_config.get("port", self.MYSQL_PORT)
                            self.MYSQL_USER = mysql_config.get("user", self.MYSQL_USER)
                            self.MYSQL_PASSWORD = mysql_config.get(
                                "password", self.MYSQL_PASSWORD
                            )
                            self.MYSQL_DB = mysql_config.get("db", self.MYSQL_DB)
                            self.MYSQL_CHARSET = mysql_config.get(
                                "charset", self.MYSQL_CHARSET
                            )

                    if config.get("upload"):
                        self.UPLOAD_DIR = config["upload"].get("dir", self.UPLOAD_DIR)
                        self.PREVIEW_DIR = config["upload"].get(
                            "preview_dir", self.PREVIEW_DIR
                        )
                        self.MAX_UPLOAD_SIZE = config["upload"].get(
                            "max_size", self.MAX_UPLOAD_SIZE
                        )

                    if config.get("douyin"):
                        self.DOUYIN_API_TIMEOUT = config["douyin"].get(
                            "api_timeout", self.DOUYIN_API_TIMEOUT
                        )
                        self.MAX_RETRY_COUNT = config["douyin"].get(
                            "max_retry_count", self.MAX_RETRY_COUNT
                        )
                        self.RETRY_DELAY = config["douyin"].get(
                            "retry_delay", self.RETRY_DELAY
                        )

                    if config.get("ai_services"):
                        self.RUNWAY_API_KEY = config["ai_services"].get(
                            "runway_api_key", self.RUNWAY_API_KEY
                        )
                        self.COQUI_API_KEY = config["ai_services"].get(
                            "coqui_api_key", self.COQUI_API_KEY
                        )
                        self.SADTALKER_API_KEY = config["ai_services"].get(
                            "sadtalker_api_key", self.SADTALKER_API_KEY
                        )

                    # 确保目录存在
                    os.makedirs(self.UPLOAD_DIR, exist_ok=True)
                    os.makedirs(self.PREVIEW_DIR, exist_ok=True)

                    logger.info("成功加载配置文件")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    def update_db_urls(self):
        """更新数据库URL"""
        if self.DB_TYPE.lower() == "sqlite":
            # SQLite配置
            db_path = os.path.abspath(self.DB_FILE)
            self.DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
            self.SYNC_DATABASE_URL = f"sqlite:///{db_path}"
            logger.info(f"使用SQLite数据库: {db_path}")
        elif self.DB_TYPE.lower() == "mysql":
            # MySQL配置
            self.DATABASE_URL = (
                f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
                f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset={self.MYSQL_CHARSET}"
            )
            self.SYNC_DATABASE_URL = (
                f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
                f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset={self.MYSQL_CHARSET}"
            )
            logger.info(
                f"使用MySQL数据库: {self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
            )
        else:
            # 默认使用SQLite
            logger.warning(f"不支持的数据库类型: {self.DB_TYPE}，默认使用SQLite")
            db_path = os.path.abspath(self.DB_FILE)
            self.DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
            self.SYNC_DATABASE_URL = f"sqlite:///{db_path}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# 全局设置实例
settings = get_settings()

# 确保必要的目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PREVIEW_DIR, exist_ok=True)

# 打印配置信息
logger.info(f"项目名称: {settings.PROJECT_NAME}")
logger.info(f"API版本: {settings.API_V1_STR}")
logger.info(f"数据库URL: {settings.DATABASE_URL}")
logger.info(f"上传目录: {settings.UPLOAD_DIR}")
logger.info(f"结果目录: {settings.RESULT_DIR}")
logger.info(f"临时目录: {settings.TEMP_DIR}")
logger.info(f"静态文件目录: {settings.STATIC_DIR}")
logger.info(f"队列大小: {settings.QUEUE_SIZE}")
logger.info(f"默认字幕擦除服务URL: {settings.DEFAULT_SUBTITLE_REMOVAL_URL}")
logger.info(f"默认语音合成服务URL: {settings.DEFAULT_VOICE_SYNTHESIS_URL}")
logger.info(f"默认唇形同步服务URL: {settings.DEFAULT_LIP_SYNC_URL}")
