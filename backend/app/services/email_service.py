"""邮件服务层。"""

from __future__ import annotations

import json
import logging
from typing import List, Optional

from app.crud.email_account_crud import EmailAccountCrud
from app.crud.email_crud import EmailCrud
from app.crud.mailbox_crud import MailboxCrud
from app.schemas.email_schema import (
    EmailListResponse,
    EmailItem,
    EmailDetailResponse,
    EmailDetail,
    SendEmailRequest,
    SendEmailResponse,
    MarkAsReadResponse,
)
from app.utils.imap import SmtpClient, ImapConfigFactory


class EmailService:
    """邮件服务类。

    负责邮件的获取、发送等业务逻辑。
    """

    def __init__(
        self,
        email_crud: EmailCrud,
        email_account_crud: EmailAccountCrud,
        mailbox_crud: MailboxCrud,
        logger: logging.Logger,
    ) -> None:
        """初始化邮件服务。

        Args:
            email_crud: 邮件数据访问对象。
            email_account_crud: 邮箱账户数据访问对象。
            mailbox_crud: 邮箱文件夹数据访问对象。
            logger: 日志记录器。
        """
        self._email_crud = email_crud
        self._email_account_crud = email_account_crud
        self._mailbox_crud = mailbox_crud
        self._logger = logger

    async def get_emails(
        self,
        user_id: int,
        account_id: Optional[int] = None,
        mailbox_id: Optional[int] = None,
        folder: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> EmailListResponse:
        """获取邮件列表。

        Args:
            user_id: 用户ID。
            account_id: 邮箱账户ID（可选，不指定则聚合所有邮箱）。
            mailbox_id: 文件夹ID（可选，不指定默认使用INBOX）。
            folder: 邮件文件夹（inbox: 收件箱, phishing: 钓鱼邮件）。
            limit: 返回数量限制。
            offset: 偏移量。

        Returns:
            邮件列表响应。
        """
        accounts = await self._email_account_crud.get_by_user_id(user_id)
        account_map = {acc.id: acc.email_address for acc in accounts}

        if not accounts:
            return EmailListResponse(success=True, emails=[], total=0)

        if account_id and account_id not in account_map:
            return EmailListResponse(success=True, emails=[], total=0)

        mailbox_ids, mailbox_name_map = await self._resolve_mailboxes(
            account_ids=[account_id] if account_id else list(account_map.keys()),
            mailbox_id=mailbox_id,
        )
        if not mailbox_ids:
            return EmailListResponse(success=True, emails=[], total=0)

        mailbox_messages = await self._email_crud.get_by_mailbox_ids(
            mailbox_ids, limit, offset
        )

        items = []
        for mailbox_message in mailbox_messages:
            message = mailbox_message.message
            if not message:
                continue
            
            phishing_score = message.phishing_score or 0.0
            
            # 根据文件夹过滤邮件
            if folder:
                if folder == 'inbox':
                    # 收件箱：钓鱼概率 < 60%
                    if phishing_score >= 0.6:
                        continue
                elif folder == 'phishing':
                    # 钓鱼邮件：钓鱼概率 >= 60%
                    if phishing_score < 0.6:
                        continue
            
            items.append(
                EmailItem(
                    id=mailbox_message.id,
                    email_account_id=message.email_account_id,
                    email_address=account_map.get(message.email_account_id),
                    mailbox_id=mailbox_message.mailbox_id,
                    mailbox_name=mailbox_name_map.get(mailbox_message.mailbox_id),
                    subject=message.subject,
                    sender=self._format_sender(
                        message.sender_name, message.sender_address
                    ),
                    snippet=message.snippet,
                    received_at=self._format_datetime(
                        mailbox_message.internal_date or message.received_at
                    ),
                    is_read=mailbox_message.is_read,
                    phishing_level=message.phishing_level.value,
                    phishing_score=phishing_score,
                    phishing_status=(
                        message.phishing_status.value
                        if message.phishing_status
                        else "COMPLETED"
                    ),
                )
            )

        return EmailListResponse(success=True, emails=items, total=len(items))

    async def get_email_detail(
        self, user_id: int, email_id: int
    ) -> EmailDetailResponse:
        """获取邮件详情。

        Args:
            user_id: 用户ID。
            email_id: 邮件ID。

        Returns:
            邮件详情响应。
        """
        mailbox_message = await self._email_crud.get_by_id(email_id)
        if not mailbox_message or not mailbox_message.message:
            return EmailDetailResponse(success=False, email=None)

        account = await self._email_account_crud.get_by_id(
            mailbox_message.message.email_account_id
        )
        if not account or account.user_id != user_id:
            return EmailDetailResponse(success=False, email=None)

        if not mailbox_message.is_read:
            await self._email_crud.mark_as_read(email_id)

        message = mailbox_message.message
        body = message.body
        recipients_json = self._serialize_recipients(message.recipients)

        detail = EmailDetail(
            id=mailbox_message.id,
            email_account_id=message.email_account_id,
            email_address=account.email_address,
            mailbox_id=mailbox_message.mailbox_id,
            mailbox_name=(
                mailbox_message.mailbox.name if mailbox_message.mailbox else None
            ),
            message_id=message.message_id or "",
            subject=message.subject,
            sender=self._format_sender(message.sender_name, message.sender_address),
            recipients=recipients_json,
            content_text=body.content_text if body else None,
            content_html=body.content_html if body else None,
            received_at=self._format_datetime(
                mailbox_message.internal_date or message.received_at
            ),
            is_read=True,
            phishing_level=message.phishing_level.value,
            phishing_score=message.phishing_score,
            phishing_reason=message.phishing_reason,
            phishing_status=(
                message.phishing_status.value
                if message.phishing_status
                else "COMPLETED"
            ),
        )

        return EmailDetailResponse(success=True, email=detail)

    async def send_email(
        self, user_id: int, request: SendEmailRequest
    ) -> SendEmailResponse:
        """发送邮件。

        Args:
            user_id: 用户ID。
            request: 发送邮件请求。

        Returns:
            发送邮件响应。
        """
        if SmtpClient is None:
            return SendEmailResponse(
                success=False,
                message="SMTP依赖未安装，请先安装aiosmtplib。",
            )

        account = await self._email_account_crud.get_by_id(request.email_account_id)
        if not account or account.user_id != user_id:
            return SendEmailResponse(
                success=False,
                message="发件邮箱账户不存在。",
            )

        password = self._email_account_crud.decrypt_password(
            account.auth_password_encrypted
        )

        config = ImapConfigFactory.get_config_or_default(
            email_type=account.email_type,
            imap_host=account.imap_host,
            imap_port=account.imap_port,
            smtp_host=account.smtp_host,
            smtp_port=account.smtp_port,
            use_ssl=account.use_ssl,
        )

        smtp_client = SmtpClient(config, self._logger)
        success = await smtp_client.send_email(
            username=account.email_address,
            password=password,
            to_addresses=request.to_addresses,
            subject=request.subject,
            content=request.content,
            content_html=request.content_html,
            cc_addresses=request.cc_addresses,
        )

        if success:
            self._logger.info(
                "发送邮件成功: from=%s, to=%s",
                account.email_address,
                request.to_addresses,
            )
            return SendEmailResponse(
                success=True,
                message="邮件发送成功。",
            )

        return SendEmailResponse(
            success=False,
            message="邮件发送失败，请稍后重试。",
        )

    async def mark_as_read(self, user_id: int, email_id: int) -> MarkAsReadResponse:
        """标记邮件为已读。

        Args:
            user_id: 用户ID。
            email_id: 邮件ID。

        Returns:
            标记已读响应。
        """
        mailbox_message = await self._email_crud.get_by_id(email_id)
        if not mailbox_message or not mailbox_message.message:
            return MarkAsReadResponse(success=False, message="邮件不存在。")

        account = await self._email_account_crud.get_by_id(
            mailbox_message.message.email_account_id
        )
        if not account or account.user_id != user_id:
            return MarkAsReadResponse(success=False, message="邮件不存在。")

        await self._email_crud.mark_as_read(email_id)

        return MarkAsReadResponse(success=True, message="标记成功。")

    async def _resolve_mailboxes(
        self, account_ids: List[int], mailbox_id: Optional[int]
    ) -> tuple[List[int], dict]:
        """解析文件夹范围。"""
        if mailbox_id:
            mailbox = await self._mailbox_crud.get_by_id(mailbox_id)
            if not mailbox or mailbox.email_account_id not in account_ids:
                return [], {}
            return [mailbox.id], {mailbox.id: mailbox.name}

        mailboxes = await self._mailbox_crud.get_inbox_by_account_ids(account_ids)
        return [mb.id for mb in mailboxes], {mb.id: mb.name for mb in mailboxes}

    def _serialize_recipients(self, recipients) -> Optional[str]:
        """序列化收件人列表为JSON字符串。"""
        if not recipients:
            return None
        payload = [
            {
                "type": recipient.recipient_type.value,
                "name": recipient.display_name,
                "address": recipient.email_address,
            }
            for recipient in recipients
        ]
        return json.dumps(payload, ensure_ascii=True)

    def _format_sender(self, name: Optional[str], address: Optional[str]) -> str:
        """格式化发件人展示名称。"""
        if name and address:
            return f"{name} <{address}>"
        return address or name or ""

    def _format_datetime(self, value) -> Optional[str]:
        """格式化日期为ISO字符串。"""
        return value.isoformat() if value else None