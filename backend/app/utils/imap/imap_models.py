"""IMAP同步相关的数据模型。"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.entities.email_recipient_entity import RecipientType


@dataclass(frozen=True)
class MailboxInfo:
    """邮箱文件夹信息。

    Attributes:
        name: 文件夹名称。
        delimiter: 层级分隔符。
        attributes: IMAP属性字符串。
    """

    name: str
    delimiter: Optional[str]
    attributes: Optional[str]


@dataclass(frozen=True)
class MailboxStatus:
    """邮箱文件夹状态信息。

    Attributes:
        uid_validity: UID有效期。
        uid_next: 下一个可用UID。
        message_count: 邮件总数。
    """

    uid_validity: Optional[int]
    uid_next: Optional[int]
    message_count: Optional[int]


@dataclass(frozen=True)
class FetchedEmail:
    """IMAP拉取到的原始邮件数据。

    Attributes:
        uid: IMAP UID。
        flags: IMAP标志位列表。
        internal_date: IMAP内部日期。
        size: 邮件大小。
        raw_bytes: 原始邮件字节。
    """

    uid: int
    flags: List[str]
    internal_date: Optional[datetime]
    size: Optional[int]
    raw_bytes: bytes


@dataclass(frozen=True)
class ParsedRecipient:
    """解析后的收件人信息。

    Attributes:
        recipient_type: 收件人类型。
        name: 显示名称。
        address: 邮箱地址。
    """

    recipient_type: RecipientType
    name: Optional[str]
    address: str


@dataclass(frozen=True)
class ParsedEmail:
    """解析后的邮件内容。

    Attributes:
        message_id: Message-ID。
        subject: 邮件主题。
        sender_name: 发件人姓名。
        sender_address: 发件人邮箱。
        recipients: 收件人列表。
        content_text: 纯文本内容。
        content_html: HTML内容。
        received_at: 邮件日期。
        snippet: 列表摘要。
    """

    message_id: Optional[str]
    subject: Optional[str]
    sender_name: Optional[str]
    sender_address: Optional[str]
    recipients: List[ParsedRecipient]
    content_text: Optional[str]
    content_html: Optional[str]
    received_at: Optional[datetime]
    snippet: Optional[str]
