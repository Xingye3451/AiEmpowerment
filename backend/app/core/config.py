from pydantic import BaseSettings
from typing import Optional, List
import os
from functools import lru_cache
import yaml
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # 配置文件路径
    config_file: str = os.getenv("CONFIG_FILE", "config/default.yaml")
    
    # 基础配置
    PROJECT_NAME: str = "AiEmpowerment"
    API_V1_STR: str = "/api/v1"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_TOKEN_EXPIRE_MINUTES: int = 120  # 管理员token默认有效期2小时
    
    # 数据库配置
    DB_FILE: str = "app.db"
    DATABASE_URL: str = ""
    SYNC_DATABASE_URL: str = ""
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads/videos"
    PREVIEW_DIR: str = "static/previews"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 抖音相关配置
    DOUYIN_API_TIMEOUT: int = 30
    MAX_RETRY_COUNT: int = 3
    RETRY_DELAY: List[int] = [60, 300, 900]  # 重试延迟：1分钟、5分钟、15分钟

    # AI服务API配置
    RUNWAY_API_KEY: str = ""
    COQUI_API_KEY: str = ""
    SADTALKER_API_KEY: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_yaml_config()
        self.update_db_urls()

    def load_yaml_config(self):
        """从YAML文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                    # 更新配置
                    if config.get('project'):
                        self.PROJECT_NAME = config['project'].get('name', self.PROJECT_NAME)
                        self.API_V1_STR = config['project'].get('api_prefix', self.API_V1_STR)
                    
                    if config.get('security'):
                        self.SECRET_KEY = config['security'].get('secret_key', self.SECRET_KEY)
                        self.ALGORITHM = config['security'].get('algorithm', self.ALGORITHM)
                        self.ACCESS_TOKEN_EXPIRE_MINUTES = config['security'].get('access_token_expire_minutes', self.ACCESS_TOKEN_EXPIRE_MINUTES)
                        self.ADMIN_TOKEN_EXPIRE_MINUTES = config['security'].get('admin_token_expire_minutes', self.ADMIN_TOKEN_EXPIRE_MINUTES)
                    
                    if config.get('database'):
                        self.DB_FILE = config['database'].get('file', self.DB_FILE)
                    
                    if config.get('upload'):
                        self.UPLOAD_DIR = config['upload'].get('dir', self.UPLOAD_DIR)
                        self.PREVIEW_DIR = config['upload'].get('preview_dir', self.PREVIEW_DIR)
                        self.MAX_UPLOAD_SIZE = config['upload'].get('max_size', self.MAX_UPLOAD_SIZE)
                    
                    if config.get('douyin'):
                        self.DOUYIN_API_TIMEOUT = config['douyin'].get('api_timeout', self.DOUYIN_API_TIMEOUT)
                        self.MAX_RETRY_COUNT = config['douyin'].get('max_retry_count', self.MAX_RETRY_COUNT)
                        self.RETRY_DELAY = config['douyin'].get('retry_delay', self.RETRY_DELAY)
                    
                    if config.get('ai_services'):
                        self.RUNWAY_API_KEY = config['ai_services'].get('runway_api_key', self.RUNWAY_API_KEY)
                        self.COQUI_API_KEY = config['ai_services'].get('coqui_api_key', self.COQUI_API_KEY)
                        self.SADTALKER_API_KEY = config['ai_services'].get('sadtalker_api_key', self.SADTALKER_API_KEY)
                    
                    # 确保目录存在
                    os.makedirs(self.UPLOAD_DIR, exist_ok=True)
                    os.makedirs(self.PREVIEW_DIR, exist_ok=True)
                    
                    logger.info("成功加载配置文件")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    def update_db_urls(self):
        """更新数据库URL"""
        db_path = os.path.abspath(self.DB_FILE)
        self.DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
        self.SYNC_DATABASE_URL = f"sqlite:///{db_path}"

    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# 全局设置实例
settings = get_settings()