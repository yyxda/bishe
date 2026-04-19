"""系统设置服务层。"""

from __future__ import annotations

import logging
import time
from typing import Optional

from app.crud.system_settings_crud import SystemSettingsCrud
from app.entities.system_settings_entity import SystemSettingsEntity


class SystemSettingsService:
    """系统设置服务类。

    提供系统设置的读取、更新以及缓存能力，降低频繁读取的数据库开销。
    """

    def __init__(
        self,
        settings_crud: SystemSettingsCrud,
        logger: logging.Logger,
        cache_ttl_seconds: int = 30,
    ) -> None:
        """初始化系统设置服务。

        Args:
            settings_crud: 系统设置CRUD实例。
            logger: 日志记录器。
            cache_ttl_seconds: 缓存过期秒数，默认30秒。
        """
        self._settings_crud = settings_crud
        self._logger = logger
        self._cache_ttl_seconds = max(cache_ttl_seconds, 1)
        self._cached_settings: Optional[SystemSettingsEntity] = None
        self._cache_expires_at = 0.0

    async def get_settings(self, force_refresh: bool = False) -> SystemSettingsEntity:
        """获取系统设置，必要时刷新缓存。

        Args:
            force_refresh: 是否强制刷新缓存。

        Returns:
            系统设置实体。
        """
        now = time.monotonic()
        if (
            not force_refresh
            and self._cached_settings is not None
            and now < self._cache_expires_at
        ):
            return self._cached_settings

        settings = await self._settings_crud.get_or_create_default()
        self._cached_settings = settings
        self._cache_expires_at = now + self._cache_ttl_seconds
        return settings

    async def update_settings(
        self,
        enable_long_url_detection: Optional[bool] = None,
        enable_rule_based_detection: Optional[bool] = None,
    ) -> SystemSettingsEntity:
        """更新系统设置并刷新缓存。

        Args:
            enable_long_url_detection: 是否启用长链接检测。
            enable_rule_based_detection: 是否启用规则检测（BERT + 规则混合检测）。

        Returns:
            更新后的系统设置实体。
        """
        settings = await self._settings_crud.update_settings(
            enable_long_url_detection=enable_long_url_detection,
            enable_rule_based_detection=enable_rule_based_detection
        )
        self._cached_settings = settings
        self._cache_expires_at = time.monotonic() + self._cache_ttl_seconds

        self._logger.info(
            "系统设置已更新: enable_long_url_detection=%s, enable_rule_based_detection=%s",
            settings.enable_long_url_detection,
            settings.enable_rule_based_detection,
        )

        return settings

    async def is_long_url_detection_enabled(self) -> bool:
        """判断是否启用长链接检测。

        Returns:
            是否启用长链接检测。
        """
        settings = await self.get_settings()
        return settings.enable_long_url_detection

    def get_cached_long_url_detection_enabled(self, default: bool = True) -> bool:
        """获取缓存中的长链接检测开关状态。

        Args:
            default: 缓存不存在时的默认值。

        Returns:
            长链接检测开关状态。
        """
        if self._cached_settings is None:
            return default
        return self._cached_settings.enable_long_url_detection

    async def is_rule_based_detection_enabled(self) -> bool:
        """判断是否启用规则检测（BERT + 规则混合检测）。

        Returns:
            是否启用规则检测。
        """
        settings = await self.get_settings()
        return settings.enable_rule_based_detection

    def get_cached_rule_based_detection_enabled(self, default: bool = False) -> bool:
        """获取缓存中的规则检测开关状态。

        Args:
            default: 缓存不存在时的默认值。

        Returns:
            规则检测开关状态。
        """
        if self._cached_settings is None:
            return default
        return self._cached_settings.enable_rule_based_detection