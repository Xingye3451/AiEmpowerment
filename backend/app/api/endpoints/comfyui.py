from fastapi import APIRouter, HTTPException, Depends, Body, Query, Request, Response
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import httpx
import json
from datetime import datetime
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
import io

from app.db.database import get_db
from app.models.comfyui import ComfyUIWorkflow
from app.core.deps import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter()

# ComfyUI服务URL配置，实际应用中应从配置文件或环境变量中读取
COMFYUI_URL = (
    settings.COMFYUI_URL
    if hasattr(settings, "COMFYUI_URL")
    else "http://127.0.0.1:8188"
)


class WorkflowCreate(BaseModel):
    name: str
    data: Dict[str, Any]
    description: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    user_id: int


class ConnectionResponse(BaseModel):
    connected: bool
    message: str


class ProxyUrlResponse(BaseModel):
    url: str


@router.get("/proxy-url", response_model=ProxyUrlResponse)
async def get_proxy_url(current_user: User = Depends(get_current_user)):
    """
    获取ComfyUI代理URL
    """
    return ProxyUrlResponse(url=f"/api/comfyui/proxy")


@router.get("/check-connection", response_model=ConnectionResponse)
async def check_connection(current_user: User = Depends(get_current_user)):
    """
    检查与ComfyUI服务的连接状态
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{COMFYUI_URL}/system_stats")
            if response.status_code == 200:
                return ConnectionResponse(
                    connected=True, message="成功连接到ComfyUI服务"
                )
            else:
                return ConnectionResponse(
                    connected=False,
                    message=f"无法连接到ComfyUI服务: {response.status_code}",
                )
    except Exception as e:
        return ConnectionResponse(
            connected=False, message=f"连接ComfyUI服务时出错: {str(e)}"
        )


@router.get("/workflows", response_model=List[WorkflowResponse])
async def get_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取当前用户保存的所有ComfyUI工作流
    """
    workflows = (
        db.query(ComfyUIWorkflow)
        .filter(ComfyUIWorkflow.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return workflows


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建新的ComfyUI工作流
    """
    db_workflow = ComfyUIWorkflow(
        name=workflow.name,
        description=workflow.description,
        data=workflow.data,
        user_id=current_user.id,
    )

    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)

    return db_workflow


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定ID的工作流
    """
    workflow = (
        db.query(ComfyUIWorkflow)
        .filter(
            ComfyUIWorkflow.id == workflow_id,
            ComfyUIWorkflow.user_id == current_user.id,
        )
        .first()
    )

    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    return workflow


@router.delete("/workflows/{workflow_id}", response_model=dict)
async def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除指定ID的工作流
    """
    workflow = (
        db.query(ComfyUIWorkflow)
        .filter(
            ComfyUIWorkflow.id == workflow_id,
            ComfyUIWorkflow.user_id == current_user.id,
        )
        .first()
    )

    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    db.delete(workflow)
    db.commit()

    return {"message": "工作流已成功删除"}


@router.post("/execute", response_model=Dict[str, Any])
async def execute_workflow(
    workflow: Dict[str, Any] = Body(..., description="要执行的工作流数据"),
    current_user: User = Depends(get_current_user),
):
    """
    在ComfyUI服务上执行指定的工作流
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COMFYUI_URL}/api/queue", json={"prompt": workflow}
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"执行工作流失败: {response.text}",
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行工作流时出错: {str(e)}")


@router.get("/results/{run_id}", response_model=Dict[str, Any])
async def get_execution_results(
    run_id: str, current_user: User = Depends(get_current_user)
):
    """
    获取指定运行ID的执行结果
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{COMFYUI_URL}/api/history/{run_id}")

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"获取执行结果失败: {response.text}",
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行结果时出错: {str(e)}")


@router.api_route(
    "/proxy/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
)
async def proxy_comfyui(
    request: Request, path: str, current_user: User = Depends(get_current_user)
):
    """
    代理所有ComfyUI请求
    """
    target_url = f"{COMFYUI_URL}/{path}"

    # 获取请求内容
    body = await request.body()
    headers = dict(request.headers)

    # 移除不需要的头部
    headers.pop("host", None)
    headers.pop("connection", None)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                follow_redirects=True,
            )

            # 创建响应
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代理请求失败: {str(e)}")
