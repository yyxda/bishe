"""钓鱼检测相关Schema。"""

from pydantic import BaseModel
from typing import Optional, Any, Dict


class VerifyLinkRequest(BaseModel):
    """链接验证请求。"""

    student_id: str
    link_url: str


class VerifyLinkResponse(BaseModel):
    """链接验证响应。"""

    success: bool
    message: str
    link_url: Optional[str] = None


class PhishingStatsResponse(BaseModel):
    """钓鱼检测统计响应。"""

    total_emails: int
    normal_count: int
    suspicious_count: int
    high_risk_count: int


class PhishingModelInfoResponse(BaseModel):
    """钓鱼模型信息响应。"""

    success: bool
    model_info: Dict[str, Any]


class PhishingReloadResponse(BaseModel):
    """钓鱼模型重载响应。"""

    success: bool
    message: str
