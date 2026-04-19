"""动态钓鱼检测器模块。

根据系统设置动态启用或关闭长链接检测。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.services.system_settings_service import SystemSettingsService
from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingResult,
)
from app.utils.phishing.composite_detector import CompositePhishingDetector


class DynamicPhishingDetector(PhishingDetectorInterface):
    """动态钓鱼检测器。

    - 长链接检测开关开启时：组合检测（长链接 + ML）。
    - 长链接检测开关关闭时：仅执行ML检测。
    """

    def __init__(
        self,
        ml_detector: PhishingDetectorInterface,
        long_url_detector: PhishingDetectorInterface,
        settings_service: SystemSettingsService,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """初始化动态检测器。

        Args:
            ml_detector: 机器学习检测器。
            long_url_detector: 长链接检测器。
            settings_service: 系统设置服务。
            logger: 日志记录器。
        """
        self._ml_detector = ml_detector
        self._long_url_detector = long_url_detector
        self._settings_service = settings_service
        self._logger = logger or logging.getLogger(self.__class__.__name__)

        self._full_detector = CompositePhishingDetector(
            detectors=[long_url_detector, ml_detector],
            logger=self._logger,
        )

    async def detect(
        self,
        subject: Optional[str],
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
        headers: Optional[Dict[str, str]] = None,
    ) -> PhishingResult:
        """检测邮件是否为钓鱼邮件。

        Args:
            subject: 邮件主题。
            sender: 发件人。
            content_text: 纯文本内容。
            content_html: HTML内容。
            headers: 邮件头信息（可选）。

        Returns:
            钓鱼检测结果。
        """
        enabled = await self._settings_service.is_long_url_detection_enabled()
        detector = self._full_detector if enabled else self._ml_detector

        self._logger.info(
            "动态检测器选择: long_url_enabled=%s, detector=%s",
            enabled,
            detector.__class__.__name__,
        )

        return await detector.detect(
            subject=subject,
            sender=sender,
            content_text=content_text,
            content_html=content_html,
            headers=headers,
        )

    async def batch_detect(
        self,
        emails: List[Dict[str, Any]],
    ) -> List[PhishingResult]:
        """批量检测邮件。

        Args:
            emails: 邮件列表。

        Returns:
            钓鱼检测结果列表。
        """
        enabled = await self._settings_service.is_long_url_detection_enabled()
        detector = self._full_detector if enabled else self._ml_detector
        return await detector.batch_detect(emails)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息。

        Returns:
            模型信息字典。
        """
        long_url_enabled = self._settings_service.get_cached_long_url_detection_enabled()
        return {
            "model_version": "dynamic-detector-1.0.0",
            "mode": "dynamic",
            "long_url_detection_enabled": long_url_enabled,
            "ml_detector": self._ml_detector.get_model_info(),
            "long_url_detector": self._long_url_detector.get_model_info(),
        }

    async def reload_model(self) -> bool:
        """热加载模型。

        Returns:
            是否全部加载成功。
        """
        ml_result = await self._ml_detector.reload_model()
        url_result = await self._long_url_detector.reload_model()
        return ml_result and url_result