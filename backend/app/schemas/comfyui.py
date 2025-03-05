from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


# 基础工作流模型
class ComfyUIWorkflowBase(BaseModel):
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")


# 创建工作流请求模型
class ComfyUIWorkflowCreate(ComfyUIWorkflowBase):
    data: Dict[str, Any] = Field(..., description="工作流JSON数据")


# 更新工作流请求模型
class ComfyUIWorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    data: Optional[Dict[str, Any]] = Field(None, description="工作流JSON数据")


# 工作流响应模型
class ComfyUIWorkflowResponse(ComfyUIWorkflowBase):
    id: int
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    user_id: str

    class Config:
        orm_mode = True


# 连接检查响应模型
class ConnectionCheckResponse(BaseModel):
    connected: bool = Field(..., description="是否成功连接")
    message: str = Field(..., description="连接状态消息")


# 执行工作流请求模型
class ExecuteWorkflowRequest(BaseModel):
    url: str = Field(..., description="ComfyUI服务URL")
    workflow: Dict[str, Any] = Field(..., description="要执行的工作流数据")


# 执行结果查询请求模型
class ExecutionResultRequest(BaseModel):
    url: str = Field(..., description="ComfyUI服务URL")
    run_id: str = Field(..., description="执行ID")
