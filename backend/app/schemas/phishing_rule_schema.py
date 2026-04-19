"""钓鱼检测规则Schema定义。"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreatePhishingRuleRequest(BaseModel):
    """创建钓鱼检测规则请求模型。"""

    rule_name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    rule_type: str = Field(
        ...,
        pattern=r"^(URL|SENDER|CONTENT|STRUCTURE)$",
        description="规则类型：URL/SENDER/CONTENT/STRUCTURE",
    )
    rule_pattern: str = Field(..., min_length=1, max_length=1000, description="规则模式（正则表达式）")
    rule_description: Optional[str] = Field(None, max_length=500, description="规则描述")
    severity: int = Field(5, ge=1, le=10, description="规则严重程度（1-10）")


class UpdatePhishingRuleRequest(BaseModel):
    """更新钓鱼检测规则请求模型。"""

    rule_name: Optional[str] = Field(None, min_length=1, max_length=100, description="规则名称")
    rule_type: Optional[str] = Field(
        None,
        pattern=r"^(URL|SENDER|CONTENT|STRUCTURE)$",
        description="规则类型",
    )
    rule_pattern: Optional[str] = Field(None, min_length=1, max_length=1000, description="规则模式")
    rule_description: Optional[str] = Field(None, max_length=500, description="规则描述")
    severity: Optional[int] = Field(None, ge=1, le=10, description="规则严重程度")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PhishingRuleResponse(BaseModel):
    """钓鱼检测规则响应模型。"""

    id: int
    rule_name: str
    rule_type: str
    rule_pattern: str
    rule_description: Optional[str] = None
    severity: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PhishingRuleListResponse(BaseModel):
    """钓鱼检测规则列表响应模型。"""

    rules: List[PhishingRuleResponse]
    total: int