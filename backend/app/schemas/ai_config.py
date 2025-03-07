from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# AI服务配置基础模型
class AIServiceConfigBase(BaseModel):
    service_type: str = Field(
        ..., description="服务类型: subtitle_removal, voice_synthesis, lip_sync"
    )
    service_name: str = Field(..., description="服务名称")
    service_url: str = Field(..., description="服务URL地址")
    is_active: bool = Field(True, description="是否启用")
    is_default: bool = Field(False, description="是否为默认服务")
    priority: int = Field(0, description="优先级，数字越小优先级越高")
    timeout: int = Field(60, description="超时时间(秒)")
    advanced_params: Optional[Dict[str, Any]] = Field(None, description="高级参数")

    # 字幕擦除特定
    auto_detect: Optional[bool] = Field(None, description="是否自动检测字幕区域")

    # 语音合成特定
    language: Optional[str] = Field(None, description="语言")
    quality: Optional[str] = Field(None, description="音质")

    # 唇形同步特定
    model_type: Optional[str] = Field(None, description="模型类型")
    batch_size: Optional[int] = Field(None, description="批处理大小")
    smooth: Optional[bool] = Field(None, description="是否平滑处理")


# 创建AI服务配置
class AIServiceConfigCreate(AIServiceConfigBase):
    pass


# 更新AI服务配置
class AIServiceConfigUpdate(BaseModel):
    service_name: Optional[str] = None
    service_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    timeout: Optional[int] = None
    advanced_params: Optional[Dict[str, Any]] = None

    # 字幕擦除特定
    auto_detect: Optional[bool] = None

    # 语音合成特定
    language: Optional[str] = None
    quality: Optional[str] = None

    # 唇形同步特定
    model_type: Optional[str] = None
    batch_size: Optional[int] = None
    smooth: Optional[bool] = None


# AI服务配置响应
class AIServiceConfigResponse(AIServiceConfigBase):
    id: int
    failure_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 系统配置基础模型
class SystemConfigBase(BaseModel):
    queue_size: int = Field(5, description="处理队列大小")
    upload_dir: str = Field("/app/uploads", description="上传目录")
    result_dir: str = Field("/app/static/results", description="结果目录")
    temp_dir: str = Field("/app/temp", description="临时目录")
    auto_clean: bool = Field(True, description="是否自动清理临时文件")
    retention_days: int = Field(30, description="保留天数")
    notify_completion: bool = Field(True, description="是否通知任务完成")
    notify_error: bool = Field(True, description="是否通知错误")
    log_level: str = Field("INFO", description="日志级别")


# 更新系统配置
class SystemConfigUpdate(SystemConfigBase):
    queue_size: Optional[int] = None
    upload_dir: Optional[str] = None
    result_dir: Optional[str] = None
    temp_dir: Optional[str] = None
    auto_clean: Optional[bool] = None
    retention_days: Optional[int] = None
    notify_completion: Optional[bool] = None
    notify_error: Optional[bool] = None
    log_level: Optional[str] = None


# 系统配置响应
class SystemConfigResponse(SystemConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 测试连接请求
class TestConnectionRequest(BaseModel):
    service_type: str
    service_url: str


# 测试连接响应
class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# 服务统计响应
class ServiceStatsResponse(BaseModel):
    service_id: int
    service_name: str
    service_type: str
    is_active: bool
    is_default: bool
    total_calls: int
    success_rate: float
    avg_response_time: float
    daily_stats: Dict[str, Dict[str, Any]]
    last_check: str
