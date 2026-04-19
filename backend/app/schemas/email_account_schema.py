"""邮箱账户相关的请求与响应模型。"""

from typing import Optional, List

from pydantic import BaseModel, Field

from app.entities.email_account_entity import EmailType


class AddEmailAccountRequest(BaseModel):
    """添加邮箱账户请求模型。"""

    email_address: str = Field(..., min_length=1, description="邮箱地址")
    email_type: EmailType = Field(..., description="邮箱类型")
    auth_password: str = Field(..., min_length=1, description="授权密码")
    imap_host: Optional[str] = Field(default=None, description="IMAP服务器地址")
    imap_port: Optional[int] = Field(default=None, description="IMAP端口")
    smtp_host: Optional[str] = Field(default=None, description="SMTP服务器地址")
    smtp_port: Optional[int] = Field(default=None, description="SMTP端口")
    use_ssl: Optional[bool] = Field(default=True, description="是否使用SSL")


class AddEmailAccountResponse(BaseModel):
    """添加邮箱账户响应模型。"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
    account_id: Optional[int] = Field(default=None, description="账户ID")
    email_address: Optional[str] = Field(default=None, description="邮箱地址")


class EmailAccountItem(BaseModel):
    """邮箱账户项模型。"""

    id: int = Field(..., description="账户ID")
    email_address: str = Field(..., description="邮箱地址")
    email_type: str = Field(..., description="邮箱类型")
    is_active: bool = Field(..., description="是否启用")
    last_sync_at: Optional[str] = Field(default=None, description="最后同步时间")


class EmailAccountListResponse(BaseModel):
    """邮箱账户列表响应模型。"""

    success: bool = Field(..., description="是否成功")
    accounts: List[EmailAccountItem] = Field(
        default_factory=list, description="账户列表"
    )


class SyncEmailsResponse(BaseModel):
    """同步邮件响应模型。"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
    synced_count: int = Field(default=0, description="同步邮件数量")


class DeleteEmailAccountResponse(BaseModel):
    """删除邮箱账户响应模型。"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")


class TestConnectionRequest(BaseModel):
    """测试连接请求模型。"""

    email_address: str = Field(..., min_length=1, description="邮箱地址")
    email_type: EmailType = Field(..., description="邮箱类型")
    auth_password: str = Field(..., min_length=1, description="授权密码")
    imap_host: Optional[str] = Field(default=None, description="IMAP服务器地址")
    imap_port: Optional[int] = Field(default=None, description="IMAP端口")
    use_ssl: Optional[bool] = Field(default=True, description="是否使用SSL")


class TestConnectionResponse(BaseModel):
    """测试连接响应模型。"""

    success: bool = Field(..., description="是否连接成功")
    message: str = Field(..., description="提示信息")
