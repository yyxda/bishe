"""邮件相关的请求与响应模型。"""

from typing import Optional, List

from pydantic import BaseModel, Field


class EmailItem(BaseModel):
    """邮件项模型。"""

    id: int = Field(..., description="邮件ID")
    email_account_id: int = Field(..., description="邮箱账户ID")
    email_address: Optional[str] = Field(default=None, description="所属邮箱地址")
    mailbox_id: Optional[int] = Field(default=None, description="文件夹ID")
    mailbox_name: Optional[str] = Field(default=None, description="文件夹名称")
    subject: Optional[str] = Field(default=None, description="邮件主题")
    sender: str = Field(..., description="发件人")
    snippet: Optional[str] = Field(default=None, description="内容摘要")
    received_at: Optional[str] = Field(default=None, description="接收时间")
    is_read: bool = Field(default=False, description="是否已读")
    phishing_level: str = Field(default="NORMAL", description="钓鱼危险等级")
    phishing_score: float = Field(default=0.0, description="钓鱼评分")
    phishing_status: str = Field(default="COMPLETED", description="钓鱼检测状态")


class EmailListResponse(BaseModel):
    """邮件列表响应模型。"""

    success: bool = Field(..., description="是否成功")
    emails: List[EmailItem] = Field(default_factory=list, description="邮件列表")
    total: int = Field(default=0, description="总数量")


class EmailDetailResponse(BaseModel):
    """邮件详情响应模型。"""

    success: bool = Field(..., description="是否成功")
    email: Optional["EmailDetail"] = Field(default=None, description="邮件详情")


class EmailDetail(BaseModel):
    """邮件详情模型。"""

    id: int = Field(..., description="邮件ID")
    email_account_id: int = Field(..., description="邮箱账户ID")
    email_address: Optional[str] = Field(default=None, description="所属邮箱地址")
    mailbox_id: Optional[int] = Field(default=None, description="文件夹ID")
    mailbox_name: Optional[str] = Field(default=None, description="文件夹名称")
    message_id: str = Field(..., description="邮件唯一标识")
    subject: Optional[str] = Field(default=None, description="邮件主题")
    sender: str = Field(..., description="发件人")
    recipients: Optional[str] = Field(default=None, description="收件人")
    content_text: Optional[str] = Field(default=None, description="纯文本内容")
    content_html: Optional[str] = Field(default=None, description="HTML内容")
    received_at: Optional[str] = Field(default=None, description="接收时间")
    is_read: bool = Field(default=False, description="是否已读")
    phishing_level: str = Field(default="NORMAL", description="钓鱼危险等级")
    phishing_score: float = Field(default=0.0, description="钓鱼评分")
    phishing_reason: Optional[str] = Field(default=None, description="钓鱼判定原因")
    phishing_status: str = Field(default="COMPLETED", description="钓鱼检测状态")


class SendEmailRequest(BaseModel):
    """发送邮件请求模型。"""

    email_account_id: int = Field(..., description="发件邮箱账户ID")
    to_addresses: List[str] = Field(..., min_length=1, description="收件人列表")
    subject: str = Field(..., description="邮件主题")
    content: str = Field(..., description="邮件内容")
    content_html: Optional[str] = Field(default=None, description="HTML内容")
    cc_addresses: Optional[List[str]] = Field(default=None, description="抄送人列表")


class SendEmailResponse(BaseModel):
    """发送邮件响应模型。"""

    success: bool = Field(..., description="是否发送成功")
    message: str = Field(..., description="提示信息")


class MarkAsReadResponse(BaseModel):
    """标记已读响应模型。"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
