from typing import List, Dict, Any, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from app.models.ai_config import AIServiceConfig, SystemConfig
from app.schemas.ai_config import (
    AIServiceConfigCreate,
    AIServiceConfigUpdate,
    SystemConfigUpdate,
)


class AIServiceConfigCRUD:
    """AI服务配置CRUD操作"""

    async def get_services(
        self, db: AsyncSession, service_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取AI服务配置列表"""
        query = select(AIServiceConfig)
        if service_type:
            query = query.where(AIServiceConfig.service_type == service_type)

        result = await db.execute(query)
        services = result.scalars().all()

        return [
            {
                "id": service.id,
                "service_type": service.service_type,
                "service_name": service.service_name,
                "service_url": service.service_url,
                "is_active": service.is_active,
                "default_mode": service.default_mode,
                "timeout": service.timeout,
                "advanced_params": service.advanced_params,
                "auto_detect": service.auto_detect,
                "language": service.language,
                "quality": service.quality,
                "model_type": service.model_type,
                "batch_size": service.batch_size,
                "smooth": service.smooth,
                "created_at": service.created_at,
                "updated_at": service.updated_at,
            }
            for service in services
        ]

    async def get_service(
        self, db: AsyncSession, service_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取单个AI服务配置"""
        service = await db.get(AIServiceConfig, service_id)
        if not service:
            return None

        return {
            "id": service.id,
            "service_type": service.service_type,
            "service_name": service.service_name,
            "service_url": service.service_url,
            "is_active": service.is_active,
            "default_mode": service.default_mode,
            "timeout": service.timeout,
            "advanced_params": service.advanced_params,
            "auto_detect": service.auto_detect,
            "language": service.language,
            "quality": service.quality,
            "model_type": service.model_type,
            "batch_size": service.batch_size,
            "smooth": service.smooth,
            "created_at": service.created_at,
            "updated_at": service.updated_at,
        }

    async def create_service(
        self, db: AsyncSession, config: AIServiceConfigCreate
    ) -> Dict[str, Any]:
        """创建AI服务配置"""
        db_service = AIServiceConfig(
            service_type=config.service_type,
            service_name=config.service_name,
            service_url=config.service_url,
            is_active=config.is_active,
            default_mode=config.default_mode,
            timeout=config.timeout,
            advanced_params=config.advanced_params,
            auto_detect=config.auto_detect,
            language=config.language,
            quality=config.quality,
            model_type=config.model_type,
            batch_size=config.batch_size,
            smooth=config.smooth,
        )

        db.add(db_service)
        await db.commit()
        await db.refresh(db_service)

        return {
            "id": db_service.id,
            "service_type": db_service.service_type,
            "service_name": db_service.service_name,
            "service_url": db_service.service_url,
            "is_active": db_service.is_active,
            "default_mode": db_service.default_mode,
            "timeout": db_service.timeout,
            "advanced_params": db_service.advanced_params,
            "auto_detect": db_service.auto_detect,
            "language": db_service.language,
            "quality": db_service.quality,
            "model_type": db_service.model_type,
            "batch_size": db_service.batch_size,
            "smooth": db_service.smooth,
            "created_at": db_service.created_at,
            "updated_at": db_service.updated_at,
        }

    async def update_service(
        self, db: AsyncSession, service_id: int, config: AIServiceConfigUpdate
    ) -> Optional[Dict[str, Any]]:
        """更新AI服务配置"""
        service = await db.get(AIServiceConfig, service_id)
        if not service:
            return None

        update_data = config.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(service, key, value)

        db.add(service)
        await db.commit()
        await db.refresh(service)

        return {
            "id": service.id,
            "service_type": service.service_type,
            "service_name": service.service_name,
            "service_url": service.service_url,
            "is_active": service.is_active,
            "default_mode": service.default_mode,
            "timeout": service.timeout,
            "advanced_params": service.advanced_params,
            "auto_detect": service.auto_detect,
            "language": service.language,
            "quality": service.quality,
            "model_type": service.model_type,
            "batch_size": service.batch_size,
            "smooth": service.smooth,
            "created_at": service.created_at,
            "updated_at": service.updated_at,
        }

    async def delete_service(self, db: AsyncSession, service_id: int) -> bool:
        """删除AI服务配置"""
        service = await db.get(AIServiceConfig, service_id)
        if not service:
            return False

        await db.delete(service)
        await db.commit()

        return True


class SystemConfigCRUD:
    """系统配置CRUD操作"""

    async def get_config(self, db: AsyncSession) -> Dict[str, Any]:
        """获取系统配置"""
        query = select(SystemConfig)
        result = await db.execute(query)
        config = result.scalars().first()

        if not config:
            # 如果没有配置，创建默认配置
            config = SystemConfig()
            db.add(config)
            await db.commit()
            await db.refresh(config)

        return {
            "id": config.id,
            "queue_size": config.queue_size,
            "upload_dir": config.upload_dir,
            "result_dir": config.result_dir,
            "temp_dir": config.temp_dir,
            "auto_clean": config.auto_clean,
            "retention_days": config.retention_days,
            "notify_completion": config.notify_completion,
            "notify_error": config.notify_error,
            "log_level": config.log_level,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

    async def update_config(
        self, db: AsyncSession, config_update: SystemConfigUpdate
    ) -> Dict[str, Any]:
        """更新系统配置"""
        query = select(SystemConfig)
        result = await db.execute(query)
        config = result.scalars().first()

        if not config:
            # 如果没有配置，创建新配置
            config = SystemConfig(**config_update.dict(exclude_unset=True))
            db.add(config)
        else:
            # 更新现有配置
            update_data = config_update.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(config, key, value)

            db.add(config)

        await db.commit()
        await db.refresh(config)

        return {
            "id": config.id,
            "queue_size": config.queue_size,
            "upload_dir": config.upload_dir,
            "result_dir": config.result_dir,
            "temp_dir": config.temp_dir,
            "auto_clean": config.auto_clean,
            "retention_days": config.retention_days,
            "notify_completion": config.notify_completion,
            "notify_error": config.notify_error,
            "log_level": config.log_level,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }


# 创建单例实例
ai_config_crud = AIServiceConfigCRUD()
system_config_crud = SystemConfigCRUD()
