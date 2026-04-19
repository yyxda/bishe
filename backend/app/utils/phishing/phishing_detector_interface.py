"""钓鱼检测器接口模块。

定义钓鱼邮件检测的抽象接口，后续可替换为真实的机器学习模型。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class PhishingLevel(str, Enum):
    """钓鱼危险等级。

    Attributes:
        NORMAL: 正常邮件。
        SUSPICIOUS: 疑似钓鱼邮件。
        HIGH_RISK: 高危钓鱼邮件。
    """

    NORMAL = "NORMAL"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"


@dataclass
class PhishingResult:
    """钓鱼检测结果。

    Attributes:
        level: 钓鱼危险等级。
        score: 钓鱼评分（0-1）。
        reason: 判定原因说明。
    """

    level: PhishingLevel
    score: float
    reason: Optional[str] = None


class PhishingDetectorInterface(ABC):
    """钓鱼检测器接口（抽象基类）。

    所有钓鱼检测实现都应该继承此接口。
    后续可以替换为真实的机器学习模型实现。
    """

    @abstractmethod
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
            headers: 邮件头信息（可选，用于高级检测）。

        Returns:
            钓鱼检测结果。
        """
        pass

    @abstractmethod
    async def batch_detect(
        self,
        emails: List[Dict[str, Any]],
    ) -> List[PhishingResult]:
        """批量检测邮件。

        Args:
            emails: 邮件列表，每项包含subject、sender、content_text、content_html。

        Returns:
            钓鱼检测结果列表。
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息。

        Returns:
            包含模型版本、路径、状态等信息的字典。
        """
        pass

    @abstractmethod
    async def reload_model(self) -> bool:
        """热加载模型（无需重启服务）。

        用于在不停止服务的情况下更新模型。

        Returns:
            加载是否成功。
        """
        pass

