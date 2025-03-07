from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
import httpx
import logging

from app.core.deps import get_db, get_current_admin
from app.models.user import User
from app.models.ai_config import AIServiceConfig, SystemConfig, ServiceUsageStats
from app.schemas.ai_config import (
    AIServiceConfigCreate,
    AIServiceConfigUpdate,
    AIServiceConfigResponse,
    SystemConfigUpdate,
    SystemConfigResponse,
    TestConnectionRequest,
    TestConnectionResponse,
    ServiceStatsResponse,
)
from app.services.ai_service_proxy import ai_service_proxy
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/services", response_model=List[AIServiceConfigResponse])
async def get_ai_services(
    service_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """获取所有AI服务配置（仅管理员）"""
    query = select(AIServiceConfig)
    if service_type:
        query = query.where(AIServiceConfig.service_type == service_type)

    result = await db.execute(query)
    services = result.scalars().all()

    return services


@router.get("/services/{service_id}", response_model=AIServiceConfigResponse)
async def get_ai_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """获取单个AI服务配置（仅管理员）"""
    query = select(AIServiceConfig).where(AIServiceConfig.id == service_id)
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务配置不存在")

    return service


@router.post("/services", response_model=AIServiceConfigResponse)
async def create_ai_service(
    service_data: AIServiceConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """创建AI服务配置（仅管理员）"""
    # 如果设置为默认服务，需要将同类型的其他服务设为非默认
    if service_data.is_default:
        query = select(AIServiceConfig).where(
            AIServiceConfig.service_type == service_data.service_type,
            AIServiceConfig.is_default == True,
        )
        result = await db.execute(query)
        default_services = result.scalars().all()

        for service in default_services:
            service.is_default = False
            db.add(service)

    # 创建新服务
    new_service = AIServiceConfig(**service_data.dict())
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)

    # 刷新服务代理缓存
    await ai_service_proxy._refresh_cache(db)

    return new_service


@router.put("/services/{service_id}", response_model=AIServiceConfigResponse)
async def update_ai_service(
    service_id: int,
    service_data: AIServiceConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """更新AI服务配置（仅管理员）"""
    query = select(AIServiceConfig).where(AIServiceConfig.id == service_id)
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务配置不存在")

    # 如果设置为默认服务，需要将同类型的其他服务设为非默认
    update_data = service_data.dict(exclude_unset=True)
    if update_data.get("is_default"):
        query = select(AIServiceConfig).where(
            AIServiceConfig.service_type == service.service_type,
            AIServiceConfig.id != service_id,
            AIServiceConfig.is_default == True,
        )
        result = await db.execute(query)
        default_services = result.scalars().all()

        for default_service in default_services:
            default_service.is_default = False
            db.add(default_service)

    # 更新服务
    for key, value in update_data.items():
        setattr(service, key, value)

    # 如果重新激活服务，重置失败计数
    if "is_active" in update_data and update_data["is_active"]:
        service.failure_count = 0

    db.add(service)
    await db.commit()
    await db.refresh(service)

    # 刷新服务代理缓存
    await ai_service_proxy._refresh_cache(db)

    return service


@router.delete("/services/{service_id}", response_model=Dict[str, str])
async def delete_ai_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """删除AI服务配置（仅管理员）"""
    query = select(AIServiceConfig).where(AIServiceConfig.id == service_id)
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务配置不存在")

    await db.delete(service)
    await db.commit()

    # 刷新服务代理缓存
    await ai_service_proxy._refresh_cache(db)

    return {"message": f"服务 {service.service_name} 已删除"}


@router.put("/services/{service_id}/set-default", response_model=Dict[str, str])
async def set_default_service(
    service_id: int,
    service_type: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """设置默认服务（仅管理员）"""
    # 先将同类型的所有服务设为非默认
    query = select(AIServiceConfig).where(AIServiceConfig.service_type == service_type)
    result = await db.execute(query)
    services = result.scalars().all()

    for service in services:
        service.is_default = False
        db.add(service)

    # 设置指定服务为默认
    query = select(AIServiceConfig).where(AIServiceConfig.id == service_id)
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")

    service.is_default = True
    db.add(service)

    await db.commit()
    await db.refresh(service)

    # 刷新服务代理缓存
    await ai_service_proxy._refresh_cache(db)

    return {"message": f"已将 {service.service_name} 设为 {service_type} 的默认服务"}


@router.post("/test-connection", response_model=Dict[str, Any])
async def test_service_connection(
    test_data: Dict[str, str] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """测试服务连接（仅管理员）"""
    service_type = test_data.get("service_type")
    service_url = test_data.get("service_url")

    if not service_type or not service_url:
        raise HTTPException(status_code=400, detail="服务类型和URL不能为空")

    try:
        # 测试连接
        async with httpx.AsyncClient(timeout=10.0) as client:
            health_url = f"{service_url.rstrip('/')}/health"
            response = await client.get(health_url)

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "连接成功",
                    "details": (
                        response.json()
                        if response.headers.get("content-type") == "application/json"
                        else None
                    ),
                }
            else:
                return {
                    "success": False,
                    "message": f"连接失败: HTTP {response.status_code}",
                    "status_code": response.status_code,
                }
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}", "error": str(e)}


@router.get("/system", response_model=SystemConfigResponse)
async def get_system_config(
    db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)
):
    """获取系统配置（仅管理员）"""
    query = select(SystemConfig)
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if not config:
        # 如果没有配置，创建默认配置
        config = SystemConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


@router.put("/system", response_model=SystemConfigResponse)
async def update_system_config(
    config_data: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """更新系统配置（仅管理员）"""
    query = select(SystemConfig)
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if not config:
        # 如果没有配置，创建新配置
        config = SystemConfig(**config_data.dict(exclude_unset=True))
        db.add(config)
    else:
        # 更新现有配置
        update_data = config_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        db.add(config)

    await db.commit()
    await db.refresh(config)

    return config


@router.get("/stats", response_model=List[ServiceStatsResponse])
async def get_service_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """获取服务使用统计（仅管理员）"""
    # 获取所有服务
    query = select(AIServiceConfig)
    result = await db.execute(query)
    services = result.scalars().all()

    # 获取指定天数内的统计数据
    start_date = datetime.utcnow().date() - timedelta(days=days)

    stats_list = []
    for service in services:
        # 获取服务统计
        query = select(ServiceUsageStats).where(
            ServiceUsageStats.service_id == service.id,
            ServiceUsageStats.date >= start_date,
        )
        result = await db.execute(query)
        stats = result.scalars().all()

        # 计算总调用次数和成功率
        total_calls = sum(stat.calls for stat in stats)
        total_success = sum(stat.success_calls for stat in stats)
        success_rate = (total_success / total_calls * 100) if total_calls > 0 else 0

        # 计算平均响应时间
        avg_response_time = (
            sum(stat.avg_response_time * stat.calls for stat in stats) / total_calls
            if total_calls > 0
            else 0
        )

        # 获取每日调用次数
        daily_calls = {
            stat.date.isoformat(): {
                "calls": stat.calls,
                "success_calls": stat.success_calls,
                "error_calls": stat.error_calls,
                "avg_response_time": stat.avg_response_time,
            }
            for stat in stats
        }

        stats_list.append(
            {
                "service_id": service.id,
                "service_name": service.service_name,
                "service_type": service.service_type,
                "is_active": service.is_active,
                "is_default": service.is_default,
                "total_calls": total_calls,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "daily_stats": daily_calls,
                "last_check": datetime.utcnow().isoformat(),
            }
        )

    return stats_list
