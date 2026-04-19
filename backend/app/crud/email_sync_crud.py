"""邮件同步写入数据访问层。"""

from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy import select

from app.core.database import DatabaseManager
from app.entities.email_body_entity import EmailBodyEntity
from app.entities.email_entity import EmailEntity, PhishingLevel, PhishingStatus
from app.entities.email_recipient_entity import EmailRecipientEntity
from app.entities.mailbox_message_entity import MailboxMessageEntity
from app.utils.imap.imap_flag_utils import flags_to_status, normalize_flags
from app.utils.imap.imap_models import ParsedRecipient
from app.utils.logging.crud_logger import CrudLogger


class EmailSyncCrud:
    """邮件同步写入CRUD操作类。

    负责批量写入邮件元数据、正文、收件人与文件夹映射。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化同步写入CRUD。

        Args:
            db_manager: 数据库管理器实例。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._crud_logger = crud_logger

    async def save_mailbox_emails(
        self,
        account_id: int,
        mailbox_id: int,
        payloads: List[Dict],
    ) -> Tuple[int, List[int]]:
        """批量写入同步邮件。

        Args:
            account_id: 邮箱账户ID。
            mailbox_id: 文件夹ID。
            payloads: 邮件数据列表。

        Returns:
            元组(新增邮件数量, 新增邮件ID列表)。
        """
        if not payloads:
            return 0, []

        message_ids = [
            payload["message_id"] for payload in payloads if payload.get("message_id")
        ]
        uids = [payload["uid"] for payload in payloads]

        async with self._db_manager.get_session() as session:
            existing_messages = await self._load_existing_messages(
                session, account_id, message_ids
            )
            existing_mailbox_messages = await self._load_existing_mailbox_messages(
                session, mailbox_id, uids
            )

            new_messages: List[EmailEntity] = []
            new_bodies: List[EmailBodyEntity] = []
            new_recipients: List[EmailRecipientEntity] = []
            new_mailbox_messages: List[MailboxMessageEntity] = []
            # 记录本次批次中已处理的message_id，避免重复创建body
            processed_message_ids: set = set()

            for payload in payloads:
                uid = payload["uid"]
                if uid in existing_mailbox_messages:
                    mailbox_message = existing_mailbox_messages[uid]
                    self._update_mailbox_message_flags(
                        mailbox_message, payload["flags"]
                    )
                    continue

                message_id = payload.get("message_id")
                message = self._get_or_create_message(
                    account_id, payload, existing_messages, new_messages
                )

                # 只有新创建的邮件（在 new_messages 中且未处理过）才创建 body 和 recipients
                if message in new_messages and message_id not in processed_message_ids:
                    new_bodies.append(
                        EmailBodyEntity(
                            message=message,
                            content_text=payload.get("content_text"),
                            content_html=payload.get("content_html"),
                        )
                    )
                    new_recipients.extend(
                        self._build_recipient_entities(
                            message, payload.get("recipients", [])
                        )
                    )
                    if message_id:
                        processed_message_ids.add(message_id)

                flags = payload.get("flags", [])
                flag_status = flags_to_status(flags)
                new_mailbox_messages.append(
                    MailboxMessageEntity(
                        mailbox_id=mailbox_id,
                        message=message,
                        uid=uid,
                        flags=normalize_flags(flags),
                        internal_date=payload.get("internal_date"),
                        is_read=flag_status["is_read"],
                        is_flagged=flag_status["is_flagged"],
                        is_answered=flag_status["is_answered"],
                        is_deleted=flag_status["is_deleted"],
                        is_draft=flag_status["is_draft"],
                    )
                )

            session.add_all(
                new_messages + new_bodies + new_recipients + new_mailbox_messages
            )
            await session.flush()

            # 获取新增邮件的ID列表（用于后台异步检测）
            new_mailbox_message_ids = [mm.id for mm in new_mailbox_messages]

            self._crud_logger.log_create(
                "同步写入邮件",
                {
                    "account_id": account_id,
                    "mailbox_id": mailbox_id,
                    "new_messages": len(new_mailbox_messages),
                },
            )

            return len(new_mailbox_messages), new_mailbox_message_ids

    async def _load_existing_messages(
        self,
        session,
        account_id: int,
        message_ids: List[str],
    ) -> Dict[str, EmailEntity]:
        """加载已存在的邮件元数据。"""
        if not message_ids:
            return {}

        query = select(EmailEntity).where(
            EmailEntity.email_account_id == account_id,
            EmailEntity.message_id.in_(message_ids),
        )
        result = await session.execute(query)
        messages = result.scalars().all()
        return {
            message.message_id: message for message in messages if message.message_id
        }

    async def _load_existing_mailbox_messages(
        self,
        session,
        mailbox_id: int,
        uids: List[int],
    ) -> Dict[int, MailboxMessageEntity]:
        """加载已存在的文件夹邮件映射。"""
        if not uids:
            return {}

        query = select(MailboxMessageEntity).where(
            MailboxMessageEntity.mailbox_id == mailbox_id,
            MailboxMessageEntity.uid.in_(uids),
        )
        result = await session.execute(query)
        mailbox_messages = result.scalars().all()
        return {item.uid: item for item in mailbox_messages}

    def _get_or_create_message(
        self,
        account_id: int,
        payload: Dict,
        existing_messages: Dict[str, EmailEntity],
        new_messages: List[EmailEntity],
    ) -> EmailEntity:
        """获取或创建邮件元数据实体。"""
        message_id = payload.get("message_id")
        if message_id and message_id in existing_messages:
            return existing_messages[message_id]

        phishing_level = payload.get("phishing_level")
        if phishing_level and isinstance(phishing_level, str):
            phishing_level = PhishingLevel(phishing_level)

        phishing_status = payload.get("phishing_status")
        if phishing_status and isinstance(phishing_status, str):
            phishing_status = PhishingStatus(phishing_status)

        message = EmailEntity(
            email_account_id=account_id,
            message_id=message_id,
            subject=payload.get("subject"),
            sender_name=payload.get("sender_name"),
            sender_address=payload.get("sender_address"),
            snippet=payload.get("snippet"),
            received_at=payload.get("received_at") or payload.get("internal_date"),
            size=payload.get("size"),
            phishing_level=phishing_level or PhishingLevel.NORMAL,
            phishing_score=payload.get("phishing_score", 0.0),
            phishing_reason=payload.get("phishing_reason"),
            phishing_status=phishing_status or PhishingStatus.PENDING,
        )
        new_messages.append(message)
        if message_id:
            existing_messages[message_id] = message
        return message

    def _build_recipient_entities(
        self, message: EmailEntity, recipients: List[ParsedRecipient]
    ) -> List[EmailRecipientEntity]:
        """构建收件人实体列表。"""
        entities: List[EmailRecipientEntity] = []
        for recipient in recipients:
            entities.append(
                EmailRecipientEntity(
                    message=message,
                    recipient_type=recipient.recipient_type,
                    display_name=recipient.name,
                    email_address=recipient.address,
                )
            )
        return entities

    def _update_mailbox_message_flags(
        self,
        mailbox_message: MailboxMessageEntity,
        flags: List[str],
    ) -> None:
        """更新邮件标志位状态。"""
        status = flags_to_status(flags)
        mailbox_message.flags = normalize_flags(flags)
        mailbox_message.is_read = status["is_read"]
        mailbox_message.is_flagged = status["is_flagged"]
        mailbox_message.is_answered = status["is_answered"]
        mailbox_message.is_deleted = status["is_deleted"]
        mailbox_message.is_draft = status["is_draft"]
