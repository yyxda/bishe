"""组合检测器模块。

管理多个钓鱼检测器，支持检测器的组合和协作。
"""

import logging
from typing import Any, Dict, List, Optional

from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingResult,
    PhishingLevel,
)


class CompositePhishingDetector(PhishingDetectorInterface):
    """组合钓鱼检测器。

    可以组合多个检测器一起工作，采用最严格的检测结果。
    面向对象设计，方便后续添加新的检测模块（如机器学习检测器）。
    """

    def __init__(
        self,
        detectors: List[PhishingDetectorInterface],
        logger: Optional[logging.Logger] = None
    ):
        """初始化组合检测器。

        Args:
            detectors: 检测器列表，按优先级排序。
            logger: 日志记录器。
        """
        if not detectors:
            raise ValueError("至少需要一个检测器")

        self._detectors = detectors
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    async def detect(
        self,
        subject: Optional[str],
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
        headers: Optional[Dict[str, str]] = None,
    ) -> PhishingResult:
        """使用所有检测器检测邮件。

        采用最严格的检测结果（最高危险等级、最高评分）。

        Args:
            subject: 邮件主题。
            sender: 发件人。
            content_text: 纯文本内容。
            content_html: HTML内容。
            headers: 邮件头信息（可选）。

        Returns:
            合并后的钓鱼检测结果。
        """
        all_results = []
        all_reasons = []

        # 运行所有检测器
        for detector in self._detectors:
            try:
                result = await detector.detect(
                    subject=subject,
                    sender=sender,
                    content_text=content_text,
                    content_html=content_html,
                    headers=headers,
                )
                all_results.append(result)

                # 收集非NORMAL的检测原因
                if result.level != PhishingLevel.NORMAL and result.reason:
                    detector_name = detector.__class__.__name__
                    all_reasons.append(f"[{detector_name}] {result.reason}")

            except Exception as e:
                self._logger.error(
                    "检测器 %s 执行失败: %s",
                    detector.__class__.__name__,
                    str(e),
                    exc_info=True
                )

        if not all_results:
            # 所有检测器都失败了，返回正常
            return PhishingResult(
                level=PhishingLevel.NORMAL,
                score=0.0,
                reason="检测器执行失败"
            )

        # 选择最严格的结果（优先级：HIGH_RISK > SUSPICIOUS > NORMAL）
        highest_level = self._get_highest_level([r.level for r in all_results])
        highest_score = max(r.score for r in all_results)

        # 合并原因
        combined_reason = "; ".join(all_reasons) if all_reasons else "未检测到明显威胁"

        self._logger.debug(
            "组合检测完成: level=%s, score=%.2f, detectors=%d",
            highest_level.value,
            highest_score,
            len(self._detectors)
        )

        return PhishingResult(
            level=highest_level,
            score=round(highest_score, 4),
            reason=combined_reason,
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
        results = []
        for email_data in emails:
            result = await self.detect(
                subject=email_data.get("subject"),
                sender=email_data.get("sender", ""),
                content_text=email_data.get("content_text"),
                content_html=email_data.get("content_html"),
                headers=email_data.get("headers"),
            )
            results.append(result)
        return results

    def get_model_info(self) -> Dict[str, Any]:
        """获取所有检测器的信息。

        Returns:
            包含所有子检测器信息的字典。
        """
        detectors_info = []
        for detector in self._detectors:
            try:
                info = detector.get_model_info()
                detectors_info.append({
                    "name": detector.__class__.__name__,
                    "info": info
                })
            except Exception as e:
                self._logger.error(
                    "获取检测器 %s 信息失败: %s",
                    detector.__class__.__name__,
                    str(e)
                )

        return {
            "model_version": "composite-detector-1.0.0",
            "mode": "composite",
            "detectors_count": len(self._detectors),
            "detectors": detectors_info,
        }

    async def reload_model(self) -> bool:
        """重新加载所有检测器。

        Returns:
            是否全部重载成功。
        """
        success_count = 0
        for detector in self._detectors:
            try:
                if await detector.reload_model():
                    success_count += 1
            except Exception as e:
                self._logger.error(
                    "重载检测器 %s 失败: %s",
                    detector.__class__.__name__,
                    str(e)
                )

        all_success = success_count == len(self._detectors)
        self._logger.info(
            "组合检测器重载完成: %d/%d 成功",
            success_count,
            len(self._detectors)
        )
        return all_success

    def add_detector(self, detector: PhishingDetectorInterface) -> None:
        """动态添加新的检测器。

        Args:
            detector: 要添加的检测器。
        """
        self._detectors.append(detector)
        self._logger.info(
            "添加检测器: %s，当前总数: %d",
            detector.__class__.__name__,
            len(self._detectors)
        )

    def remove_detector(self, detector_class_name: str) -> bool:
        """移除指定的检测器。

        Args:
            detector_class_name: 检测器类名。

        Returns:
            是否成功移除。
        """
        initial_count = len(self._detectors)
        self._detectors = [
            d for d in self._detectors
            if d.__class__.__name__ != detector_class_name
        ]
        removed = len(self._detectors) < initial_count

        if removed:
            self._logger.info("移除检测器: %s", detector_class_name)
        else:
            self._logger.warning("未找到检测器: %s", detector_class_name)

        return removed

    @staticmethod
    def _get_highest_level(levels: List[PhishingLevel]) -> PhishingLevel:
        """获取最高危险等级。

        Args:
            levels: 危险等级列表。

        Returns:
            最高的危险等级。
        """
        if PhishingLevel.HIGH_RISK in levels:
            return PhishingLevel.HIGH_RISK
        elif PhishingLevel.SUSPICIOUS in levels:
            return PhishingLevel.SUSPICIOUS
        else:
            return PhishingLevel.NORMAL
