"""钓鱼评分等级映射器。

统一将钓鱼置信度（0-1）映射为危险等级，确保前后端阈值一致。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.utils.phishing.phishing_detector_interface import PhishingLevel


@dataclass(frozen=True)
class ScoreThresholds:
    """置信度阈值配置。

    Attributes:
        suspicious_threshold: 疑似钓鱼阈值（包含）。
        high_risk_threshold: 高危阈值（包含）。
    """

    suspicious_threshold: float = 0.6
    high_risk_threshold: float = 0.75


class ScoreLevelMapper:
    """置信度到危险等级的映射器。"""

    def __init__(self, thresholds: Optional[ScoreThresholds] = None) -> None:
        """初始化映射器。

        Args:
            thresholds: 阈值配置，默认使用 60%/80%。
        """
        self._thresholds = thresholds or ScoreThresholds()

    def normalize_score(self, score: Optional[float]) -> float:
        """归一化置信度分数到 0-1。

        Args:
            score: 原始置信度分数。

        Returns:
            归一化后的分数。
        """
        try:
            value = float(score) if score is not None else 0.0
        except (TypeError, ValueError):
            value = 0.0

        return max(0.0, min(1.0, value))

    def get_level(self, score: Optional[float]) -> PhishingLevel:
        """根据置信度获取危险等级。

        Args:
            score: 置信度分数。

        Returns:
            危险等级。
        """
        normalized = self.normalize_score(score)
        if normalized >= self._thresholds.high_risk_threshold:
            return PhishingLevel.HIGH_RISK
        if normalized >= self._thresholds.suspicious_threshold:
            return PhishingLevel.SUSPICIOUS
        return PhishingLevel.NORMAL

    @property
    def suspicious_threshold(self) -> float:
        """获取疑似钓鱼阈值。"""
        return self._thresholds.suspicious_threshold

    @property
    def high_risk_threshold(self) -> float:
        """获取高危阈值。"""
        return self._thresholds.high_risk_threshold