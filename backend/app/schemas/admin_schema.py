"""管理员功能Schema定义。"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ========== 用户管理 ==========


class CreateUserRequest(BaseModel):
    """创建用户请求模型。"""

    student_id: str = Field(..., min_length=1, max_length=20, description="学号")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    display_name: str = Field(..., min_length=1, max_length=50, description="显示名称")


class UserResponse(BaseModel):
    """用户响应模型。"""

    id: int
    student_id: str
    display_name: str
    is_active: bool
    role: str
    created_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """用户列表响应模型。"""

    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class SetUserStatusRequest(BaseModel):
    """设置用户状态请求模型。"""

    is_active: bool = Field(..., description="是否启用")


# ========== URL白名单管理 ==========


class CreateWhitelistRuleRequest(BaseModel):
    """创建URL白名单规则请求模型。"""

    rule_type: str = Field(
        ...,
        pattern=r"^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD)$",
        description="规则类型",
    )
    rule_value: str = Field(..., min_length=1, max_length=255, description="规则值")
    description: Optional[str] = Field(None, max_length=500, description="规则描述")


class UpdateWhitelistRuleRequest(BaseModel):
    """更新URL白名单规则请求模型。"""

    rule_type: Optional[str] = Field(
        None,
        pattern=r"^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD)$",
        description="规则类型",
    )
    rule_value: Optional[str] = Field(
        None, min_length=1, max_length=255, description="规则值"
    )
    description: Optional[str] = Field(None, max_length=500, description="规则描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class WhitelistRuleResponse(BaseModel):
    """URL白名单规则响应模型。"""

    id: int
    rule_type: str
    rule_value: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None


class WhitelistRuleListResponse(BaseModel):
    """URL白名单规则列表响应模型。"""

    rules: List[WhitelistRuleResponse]


# ========== 发件人白名单管理 ==========


class CreateSenderWhitelistRequest(BaseModel):
    """创建发件人白名单规则请求模型。"""

    rule_type: str = Field(
        ...,
        pattern=r"^(EMAIL|DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD)$",
        description="规则类型：EMAIL(精确匹配邮箱)/DOMAIN(精确匹配域名)/DOMAIN-SUFFIX(域名后缀)/DOMAIN-KEYWORD(域名关键词)",
    )
    rule_value: str = Field(..., min_length=1, max_length=255, description="规则值")
    description: Optional[str] = Field(None, max_length=500, description="规则描述")


class UpdateSenderWhitelistRequest(BaseModel):
    """更新发件人白名单规则请求模型。"""

    rule_type: Optional[str] = Field(
        None,
        pattern=r"^(EMAIL|DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD)$",
        description="规则类型",
    )
    rule_value: Optional[str] = Field(
        None, min_length=1, max_length=255, description="规则值"
    )
    description: Optional[str] = Field(None, max_length=500, description="规则描述")
    is_active: Optional[bool] = Field(None, description="是否启用")


class SenderWhitelistResponse(BaseModel):
    """发件人白名单规则响应模型。"""

    id: int
    rule_type: str
    rule_value: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None


class SenderWhitelistListResponse(BaseModel):
    """发件人白名单规则列表响应模型。"""

    rules: List[SenderWhitelistResponse]


# ========== 系统设置 ==========


class UpdateSystemSettingsRequest(BaseModel):
    """更新系统设置请求模型。"""

    enable_long_url_detection: Optional[bool] = Field(
        None, description="是否启用长链接检测"
    )
    enable_rule_based_detection: Optional[bool] = Field(
        None, description="是否启用规则检测（BERT + 规则混合检测）"
    )


class SystemSettingsResponse(BaseModel):
    """系统设置响应模型。"""

    enable_long_url_detection: bool = Field(..., description="是否启用长链接检测")
    enable_rule_based_detection: bool = Field(..., description="是否启用规则检测（BERT + 规则混合检测）")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ========== 通用响应 ==========


class OperationResponse(BaseModel):
    """操作响应模型。"""

    success: bool
    message: str