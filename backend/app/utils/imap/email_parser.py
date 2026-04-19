"""邮件解析工具模块。"""

from __future__ import annotations

import email
import re
from dataclasses import dataclass
from datetime import datetime
from email.header import decode_header
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime
from typing import List, Optional

from app.entities.email_recipient_entity import RecipientType
from app.utils.imap.imap_models import ParsedEmail, ParsedRecipient


@dataclass(frozen=True)
class SenderInfo:
    """发件人信息。

    Attributes:
        name: 显示名称。
        address: 邮箱地址。
    """

    name: Optional[str]
    address: Optional[str]


class EmailParser:
    """邮件解析器。

    将原始邮件字节解析为结构化的字段，供同步入库使用。
    """

    def __init__(self, logger) -> None:
        """初始化解析器。

        Args:
            logger: 日志记录器。
        """
        self._logger = logger

    def parse(self, raw_email: bytes) -> Optional[ParsedEmail]:
        """解析原始邮件内容。

        Args:
            raw_email: 原始邮件字节数据。

        Returns:
            解析后的邮件对象，失败返回None。
        """
        try:
            msg = email.message_from_bytes(raw_email)

            message_id = msg.get("Message-ID") or None
            subject = self._decode_header(msg.get("Subject", ""))

            sender = self._parse_sender(msg.get("From", ""))
            recipients = self._parse_recipients(msg)

            received_at = self._parse_date(msg.get("Date"))
            content_text, content_html = self._extract_content(msg)
            snippet = self._build_snippet(content_text, content_html)

            return ParsedEmail(
                message_id=message_id,
                subject=subject,
                sender_name=sender.name,
                sender_address=sender.address,
                recipients=recipients,
                content_text=content_text,
                content_html=content_html,
                received_at=received_at,
                snippet=snippet,
            )
        except Exception as exc:
            self._logger.error("解析邮件失败: %s", exc)
            return None

    def _parse_sender(self, header_value: str) -> SenderInfo:
        """解析发件人信息。

        Args:
            header_value: From头部原始值。

        Returns:
            发件人信息对象。
        """
        decoded = self._decode_header(header_value)
        addresses = getaddresses([decoded])
        if not addresses:
            return SenderInfo(name=None, address=None)

        name, address = addresses[0]
        return SenderInfo(name=name or None, address=address or None)

    def _parse_recipients(self, msg: Message) -> List[ParsedRecipient]:
        """解析收件人信息。

        Args:
            msg: 邮件对象。

        Returns:
            收件人列表。
        """
        recipients: List[ParsedRecipient] = []

        recipients.extend(
            self._parse_recipient_header("To", msg.get("To"), RecipientType.TO)
        )
        recipients.extend(
            self._parse_recipient_header("Cc", msg.get("Cc"), RecipientType.CC)
        )
        recipients.extend(
            self._parse_recipient_header("Bcc", msg.get("Bcc"), RecipientType.BCC)
        )
        recipients.extend(
            self._parse_recipient_header(
                "Reply-To", msg.get("Reply-To"), RecipientType.REPLY_TO
            )
        )

        return recipients

    def _parse_recipient_header(
        self,
        header_name: str,
        header_value: Optional[str],
        recipient_type: RecipientType,
    ) -> List[ParsedRecipient]:
        """解析单个收件人头部字段。

        Args:
            header_name: 头部名称，用于日志。
            header_value: 头部值。
            recipient_type: 收件人类型。

        Returns:
            收件人列表。
        """
        if not header_value:
            return []

        decoded = self._decode_header(header_value)
        addresses = getaddresses([decoded])
        recipients = []
        for name, address in addresses:
            if not address:
                continue
            recipients.append(
                ParsedRecipient(
                    recipient_type=recipient_type,
                    name=name or None,
                    address=address,
                )
            )

        if not recipients:
            self._logger.debug("未解析到收件人: header=%s", header_name)
        return recipients

    def _extract_content(self, msg: Message) -> tuple[Optional[str], Optional[str]]:
        """提取邮件正文内容。

        Args:
            msg: 邮件对象。

        Returns:
            (纯文本内容, HTML内容)。
        """
        content_text = None
        content_html = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" and not content_text:
                    payload = part.get_payload(decode=True)
                    if payload:
                        content_text = self._decode_content(payload, part)
                elif content_type == "text/html" and not content_html:
                    payload = part.get_payload(decode=True)
                    if payload:
                        content_html = self._decode_content(payload, part)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                content = self._decode_content(payload, msg)
                if msg.get_content_type() == "text/html":
                    content_html = content
                else:
                    content_text = content

        return content_text, content_html

    def _decode_header(self, header_value: str) -> str:
        """解码邮件头部内容。

        Args:
            header_value: 头部原始值。

        Returns:
            解码后的字符串。
        """
        if not header_value:
            return ""

        try:
            decoded_parts = decode_header(header_value)
            result = []
            for content, charset in decoded_parts:
                if isinstance(content, bytes):
                    result.append(content.decode(charset or "utf-8", errors="replace"))
                else:
                    result.append(content)
            return "".join(result)
        except Exception:
            return str(header_value)

    def _decode_content(self, payload: bytes, part: Message) -> str:
        """解码邮件正文。

        Args:
            payload: 邮件内容字节数据。
            part: 邮件部分对象。

        Returns:
            解码后的文本内容。
        """
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except Exception:
            return payload.decode("utf-8", errors="replace")

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析邮件日期字段。

        Args:
            date_str: 日期字符串。

        Returns:
            解析后的日期对象。
        """
        if not date_str:
            return None

        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return None

    def _build_snippet(
        self, content_text: Optional[str], content_html: Optional[str]
    ) -> Optional[str]:
        """生成邮件摘要。

        Args:
            content_text: 纯文本内容。
            content_html: HTML内容。

        Returns:
            摘要文本。
        """
        raw_text = content_text or self._strip_html(content_html or "")
        raw_text = re.sub(r"\s+", " ", raw_text or "").strip()
        if not raw_text:
            return None
        return raw_text[:200]

    def _strip_html(self, html: str) -> str:
        """移除HTML标签获取纯文本。

        Args:
            html: HTML字符串。

        Returns:
            纯文本字符串。
        """
        # Remove script and style elements and their content
        html = re.sub(
            r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE
        )
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)
        return text
