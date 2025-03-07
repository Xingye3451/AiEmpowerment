from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Float,
    JSON,
    DateTime,
    ForeignKey,
    Date,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base


class AIServiceConfig(Base):
    """AI服务配置模型"""

    __tablename__ = "ai_service_configs"

    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(
        String, index=True
    )  # 'subtitle_removal', 'voice_synthesis', 'lip_sync'
    service_name = Column(String, nullable=False)
    service_url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # 是否为默认服务
    priority = Column(Integer, default=0)  # 优先级，数字越小优先级越高
    timeout = Column(Integer, default=60)
    failure_count = Column(Integer, default=0)  # 连续失败次数
    advanced_params = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 字幕擦除特定
    auto_detect = Column(Boolean, nullable=True)

    # 语音合成特定
    language = Column(String, nullable=True)
    quality = Column(String, nullable=True)

    # 唇形同步特定
    model_type = Column(String, nullable=True)
    batch_size = Column(Integer, nullable=True)
    smooth = Column(Boolean, nullable=True)

    usage_stats = relationship("ServiceUsageStats", back_populates="service")


class SystemConfig(Base):
    """系统配置模型"""

    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    queue_size = Column(Integer, default=5)
    upload_dir = Column(String, default="/app/uploads")
    result_dir = Column(String, default="/app/static/results")
    temp_dir = Column(String, default="/app/temp")
    auto_clean = Column(Boolean, default=True)
    retention_days = Column(Integer, default=30)
    notify_completion = Column(Boolean, default=True)
    notify_error = Column(Boolean, default=True)
    log_level = Column(String, default="INFO")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ServiceUsageStats(Base):
    """服务使用统计模型"""

    __tablename__ = "service_usage_stats"

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("ai_service_configs.id"))
    date = Column(Date, default=lambda: datetime.utcnow().date())
    calls = Column(Integer, default=0)
    success_calls = Column(Integer, default=0)
    error_calls = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0)

    service = relationship("AIServiceConfig", back_populates="usage_stats")
