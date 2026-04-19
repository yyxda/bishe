"""系统设置数据访问层。"""

from typing import Optional

from sqlalchemy import select

from app.core.database import DatabaseManager
from app.entities.system_settings_entity import SystemSettingsEntity
from app.utils.logging.crud_logger import CrudLogger


class SystemSettingsCrud:
    """系统设置CRUD操作类。

    提供系统设置的读取与更新能力，确保至少存在一条默认记录。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化系统设置CRUD。

        Args:
            db_manager: 数据库管理器实例。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._crud_logger = crud_logger

    async def get_settings(self) -> Optional[SystemSettingsEntity]:
        """获取系统设置记录（可能为空）。

        Returns:
            系统设置实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(SystemSettingsEntity).order_by(SystemSettingsEntity.id.asc())
            result = await session.execute(query)
            settings = result.scalars().first()

            self._crud_logger.log_read(
                "获取系统设置",
                {"found": settings is not None},
            )

            return settings

    async def get_or_create_default(self) -> SystemSettingsEntity:
        """获取系统设置，如不存在则创建默认记录。

        Returns:
            系统设置实体。
        """
        async with self._db_manager.get_session() as session:
            query = select(SystemSettingsEntity).order_by(SystemSettingsEntity.id.asc())
            result = await session.execute(query)
            settings = result.scalars().first()

            if settings:
                self._crud_logger.log_read(
                    "获取系统设置",
                    {"created": False},
                )
                return settings

            settings = SystemSettingsEntity(
                enable_long_url_detection=True,
                enable_rule_based_detection=False
            )
            session.add(settings)
            await session.flush()
            await session.refresh(settings)

            self._crud_logger.log_create(
                "创建默认系统设置",
                {
                    "enable_long_url_detection": settings.enable_long_url_detection,
                    "enable_rule_based_detection": settings.enable_rule_based_detection
                },
            )

            return settings

    async def update_settings(
        self,
        enable_long_url_detection: Optional[bool] = None,
        enable_rule_based_detection: Optional[bool] = None,
    ) -> SystemSettingsEntity:
        """更新系统设置。

        Args:
            enable_long_url_detection: 是否启用长链接检测。
            enable_rule_based_detection: 是否启用规则检测（BERT + 规则混合检测）。

        Returns:
            更新后的系统设置实体。
        """
        async with self._db_manager.get_session() as session:
            query = select(SystemSettingsEntity).order_by(SystemSettingsEntity.id.asc())
            result = await session.execute(query)
            settings = result.scalars().first()

            if not settings:
                settings = SystemSettingsEntity(
                    enable_long_url_detection=(
                        enable_long_url_detection
                        if enable_long_url_detection is not None
                        else True
                    ),
                    enable_rule_based_detection=(
                        enable_rule_based_detection
                        if enable_rule_based_detection is not None
                        else False
                    )
                )
                session.add(settings)
                await session.flush()
                await session.refresh(settings)

                self._crud_logger.log_create(
                    "创建系统设置并更新",
                    {
                        "enable_long_url_detection": settings.enable_long_url_detection,
                        "enable_rule_based_detection": settings.enable_rule_based_detection
                    },
                )
                return settings

            if enable_long_url_detection is not None:
                settings.enable_long_url_detection = enable_long_url_detection
            if enable_rule_based_detection is not None:
                settings.enable_rule_based_detection = enable_rule_based_detection

            await session.flush()
            await session.refresh(settings)

            self._crud_logger.log_update(
                "更新系统设置",
                {
                    "enable_long_url_detection": settings.enable_long_url_detection,
                    "enable_rule_based_detection": settings.enable_rule_based_detection
                },
            )

            return settings