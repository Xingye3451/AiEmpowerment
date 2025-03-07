import time
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.ai_config import AIServiceConfig, ServiceUsageStats
import logging
from datetime import datetime

# 设置日志
logger = logging.getLogger(__name__)


class AIServiceProxy:
    def __init__(self):
        self._service_cache = {}
        self._cache_timestamp = 0

    async def _refresh_cache_if_needed(self, db: AsyncSession):
        """定期刷新服务缓存"""
        current_time = time.time()
        if current_time - self._cache_timestamp > 60:  # 每分钟刷新一次
            await self._refresh_cache(db)

    async def _refresh_cache(self, db: AsyncSession):
        """从数据库刷新服务配置缓存"""
        query = select(AIServiceConfig).where(AIServiceConfig.is_active == True)
        result = await db.execute(query)
        services = result.scalars().all()

        # 按服务类型分组
        self._service_cache = {}
        for service in services:
            if service.service_type not in self._service_cache:
                self._service_cache[service.service_type] = []

            # 提取服务特定参数
            specific_params = {}
            if (
                service.service_type == "subtitle_removal"
                and service.auto_detect is not None
            ):
                specific_params["auto_detect"] = service.auto_detect
            elif service.service_type == "voice_synthesis":
                if service.language:
                    specific_params["language"] = service.language
                if service.quality:
                    specific_params["quality"] = service.quality
            elif service.service_type == "lip_sync":
                if service.model_type:
                    specific_params["model_type"] = service.model_type
                if service.batch_size:
                    specific_params["batch_size"] = service.batch_size
                if service.smooth is not None:
                    specific_params["smooth"] = service.smooth

            self._service_cache[service.service_type].append(
                {
                    "id": service.id,
                    "name": service.service_name,
                    "url": service.service_url,
                    "is_default": service.is_default,
                    "priority": service.priority,
                    "timeout": service.timeout,
                    "params": {**(service.advanced_params or {}), **specific_params},
                }
            )

        self._cache_timestamp = time.time()
        logger.info(f"服务配置缓存已刷新，共 {len(services)} 个服务")

    async def get_services(
        self, db: AsyncSession, service_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取所有服务配置"""
        await self._refresh_cache_if_needed(db)

        if service_type:
            return self._service_cache.get(service_type, [])

        # 返回所有服务
        all_services = []
        for services in self._service_cache.values():
            all_services.extend(services)

        return all_services

    async def _get_service_for_type(self, db: AsyncSession, service_type: str):
        """获取指定类型的服务，优先返回默认服务"""
        await self._refresh_cache_if_needed(db)

        services = self._service_cache.get(service_type, [])
        if not services:
            raise ValueError(f"没有找到类型为 {service_type} 的可用服务")

        # 首先尝试找默认服务
        default_services = [s for s in services if s.get("is_default", False)]
        if default_services:
            return default_services[0]

        # 如果没有默认服务，按优先级排序
        sorted_services = sorted(services, key=lambda s: s.get("priority", 0))
        return sorted_services[0]

    async def call_service(
        self,
        db: AsyncSession,
        service_type: str,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        service_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """调用指定类型的AI服务"""
        try:
            # 获取服务
            if service_id:
                # 如果指定了服务ID，则使用指定服务
                await self._refresh_cache_if_needed(db)
                service = None
                for services in self._service_cache.values():
                    for s in services:
                        if s["id"] == service_id:
                            service = s
                            break
                    if service:
                        break

                if not service:
                    raise ValueError(f"找不到ID为 {service_id} 的服务")
            else:
                # 否则使用默认服务
                service = await self._get_service_for_type(db, service_type)

            # 记录开始时间
            start_time = time.time()

            # 构建请求URL和参数
            url = f"{service['url']}/{endpoint.lstrip('/')}"
            timeout = service["timeout"]

            # 合并高级参数
            request_data = {}
            if service["params"]:
                request_data.update(service["params"])
            if data:
                request_data.update(data)

            # 发送请求
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=request_data)
                elif method.upper() == "POST":
                    if files:
                        response = await client.post(
                            url, data=request_data, files=files
                        )
                    else:
                        response = await client.post(url, json=request_data)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")

                response.raise_for_status()

                # 记录成功调用
                response_time = time.time() - start_time
                await self._record_usage(db, service["id"], True, response_time)

                return response.json()
        except Exception as e:
            logger.error(f"调用服务 {service_type} 失败: {str(e)}")

            # 记录失败调用
            if "service" in locals() and "start_time" in locals():
                response_time = time.time() - start_time
                await self._record_usage(db, service["id"], False, response_time)
                await self._record_service_failure(db, service["id"])

            # 如果有多个服务，可以尝试其他服务
            if (
                not service_id
                and service_type in self._service_cache
                and len(self._service_cache[service_type]) > 1
            ):
                logger.info(f"尝试使用备用服务...")

                # 获取备用服务（排除当前失败的服务）
                backup_services = [
                    s
                    for s in self._service_cache[service_type]
                    if s["id"] != service["id"]
                ]

                if backup_services:
                    # 按优先级排序
                    sorted_backups = sorted(
                        backup_services, key=lambda s: s.get("priority", 0)
                    )
                    backup = sorted_backups[0]

                    logger.info(f"使用备用服务: {backup['name']}")

                    # 使用备用服务重试
                    return await self.call_service(
                        db, service_type, endpoint, method, data, files, backup["id"]
                    )

            # 如果所有尝试都失败，抛出原始异常
            raise

    async def _record_usage(
        self, db: AsyncSession, service_id: int, success: bool, response_time: float
    ):
        """记录服务使用统计"""
        today = datetime.utcnow().date()

        # 查找今天的统计记录
        query = select(ServiceUsageStats).where(
            ServiceUsageStats.service_id == service_id, ServiceUsageStats.date == today
        )
        result = await db.execute(query)
        stats = result.scalar_one_or_none()

        if not stats:
            # 创建新记录
            stats = ServiceUsageStats(
                service_id=service_id,
                date=today,
                calls=1,
                success_calls=1 if success else 0,
                error_calls=0 if success else 1,
                avg_response_time=response_time,
            )
            db.add(stats)
        else:
            # 更新现有记录
            stats.calls += 1
            if success:
                stats.success_calls += 1
            else:
                stats.error_calls += 1

            # 更新平均响应时间
            stats.avg_response_time = (
                stats.avg_response_time * (stats.calls - 1) + response_time
            ) / stats.calls
            db.add(stats)

        await db.commit()

    async def _record_service_failure(self, db: AsyncSession, service_id: int):
        """记录服务失败"""
        query = select(AIServiceConfig).where(AIServiceConfig.id == service_id)
        result = await db.execute(query)
        service = result.scalar_one_or_none()

        if service:
            # 增加连续失败次数
            service.failure_count = (service.failure_count or 0) + 1

            # 如果连续失败次数过多，可以自动禁用服务
            if service.failure_count >= 5:  # 连续失败5次后禁用
                service.is_active = False
                logger.warning(
                    f"服务 {service.service_name} 已被自动禁用，因为连续失败次数过多"
                )

            db.add(service)
            await db.commit()

    async def reset_service_failure(self, db: AsyncSession, service_id: int):
        """重置服务失败计数"""
        query = select(AIServiceConfig).where(AIServiceConfig.id == service_id)
        result = await db.execute(query)
        service = result.scalar_one_or_none()

        if service:
            service.failure_count = 0
            db.add(service)
            await db.commit()
            logger.info(f"服务 {service.service_name} 的失败计数已重置")


# 创建全局服务代理实例
ai_service_proxy = AIServiceProxy()
