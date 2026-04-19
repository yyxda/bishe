"""邮箱文件夹数据访问层。"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import delete, select

from app.core.database import DatabaseManager
from app.entities.mailbox_entity import MailboxEntity
from app.entities.mailbox_message_entity import MailboxMessageEntity
from app.utils.logging.crud_logger import CrudLogger


class MailboxCrud:
    """邮箱文件夹CRUD操作类。

    提供文件夹的增删改查与同步状态维护。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化文件夹CRUD。

        Args:
            db_manager: 数据库管理器实例。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._crud_logger = crud_logger

    async def get_by_account_id(self, account_id: int) -> List[MailboxEntity]:
        """获取邮箱账户下的文件夹列表。

        Args:
            account_id: 邮箱账户ID。

        Returns:
            文件夹实体列表。
        """
        async with self._db_manager.get_session() as session:
            query = select(MailboxEntity).where(MailboxEntity.email_account_id == account_id)
            result = await session.execute(query)
            mailboxes = result.scalars().all()

            self._crud_logger.log_read(
                "查询文件夹列表",
                {"account_id": account_id, "count": len(mailboxes)},
            )

            return list(mailboxes)

    async def get_by_id(self, mailbox_id: int) -> Optional[MailboxEntity]:
        """根据ID获取文件夹。

        Args:
            mailbox_id: 文件夹ID。

        Returns:
            文件夹实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(MailboxEntity).where(MailboxEntity.id == mailbox_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_by_account_and_name(
        self, account_id: int, name: str
    ) -> Optional[MailboxEntity]:
        """根据账户和名称获取文件夹。

        Args:
            account_id: 邮箱账户ID。
            name: 文件夹名称。

        Returns:
            文件夹实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(MailboxEntity).where(
                MailboxEntity.email_account_id == account_id,
                MailboxEntity.name == name,
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_inbox_by_account_id(self, account_id: int) -> Optional[MailboxEntity]:
        """获取账户的INBOX文件夹。

        Args:
            account_id: 邮箱账户ID。

        Returns:
            INBOX文件夹实体或None。
        """
        return await self.get_by_account_and_name(account_id, "INBOX")

    async def get_inbox_by_account_ids(
        self, account_ids: List[int]
    ) -> List[MailboxEntity]:
        """批量获取INBOX文件夹。

        Args:
            account_ids: 邮箱账户ID列表。

        Returns:
            INBOX文件夹实体列表。
        """
        if not account_ids:
            return []

        async with self._db_manager.get_session() as session:
            query = select(MailboxEntity).where(
                MailboxEntity.email_account_id.in_(account_ids),
                MailboxEntity.name == "INBOX",
            )
            result = await session.execute(query)
            return list(result.scalars().all())

    async def upsert_mailbox(
        self,
        account_id: int,
        name: str,
        delimiter: Optional[str],
        attributes: Optional[str],
        uid_validity: Optional[int],
    ) -> Tuple[MailboxEntity, bool]:
        """创建或更新文件夹信息。

        Args:
            account_id: 邮箱账户ID。
            name: 文件夹名称。
            delimiter: 分隔符。
            attributes: 属性字符串。
            uid_validity: UID有效期。

        Returns:
            (文件夹实体, 是否发生UID有效期变更)。
        """
        async with self._db_manager.get_session() as session:
            query = select(MailboxEntity).where(
                MailboxEntity.email_account_id == account_id,
                MailboxEntity.name == name,
            )
            result = await session.execute(query)
            mailbox = result.scalar_one_or_none()

            if mailbox:
                uid_changed = (
                    uid_validity is not None
                    and mailbox.uid_validity is not None
                    and mailbox.uid_validity != uid_validity
                )
                mailbox.delimiter = delimiter
                mailbox.attributes = attributes
                mailbox.uid_validity = uid_validity or mailbox.uid_validity
                if uid_changed:
                    mailbox.last_uid = 0
                await session.flush()

                self._crud_logger.log_update(
                    "更新文件夹",
                    {"account_id": account_id, "name": name, "uid_changed": uid_changed},
                )
                return mailbox, uid_changed

            mailbox = MailboxEntity(
                email_account_id=account_id,
                name=name,
                delimiter=delimiter,
                attributes=attributes,
                uid_validity=uid_validity,
                last_uid=0,
            )
            session.add(mailbox)
            await session.flush()
            await session.refresh(mailbox)

            self._crud_logger.log_create(
                "创建文件夹",
                {"account_id": account_id, "name": name},
            )

            return mailbox, False

    async def update_sync_state(
        self,
        mailbox_id: int,
        last_uid: int,
        sync_time: Optional[datetime] = None,
    ) -> bool:
        """更新文件夹同步状态。

        Args:
            mailbox_id: 文件夹ID。
            last_uid: 最后同步UID。
            sync_time: 同步时间。

        Returns:
            是否更新成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(MailboxEntity).where(MailboxEntity.id == mailbox_id)
            result = await session.execute(query)
            mailbox = result.scalar_one_or_none()

            if not mailbox:
                return False

            mailbox.last_uid = last_uid
            mailbox.last_sync_at = sync_time or datetime.now()
            await session.flush()

            self._crud_logger.log_update(
                "更新文件夹同步状态",
                {"mailbox_id": mailbox_id, "last_uid": last_uid},
            )

            return True

    async def reset_mailbox_messages(self, mailbox_id: int) -> int:
        """清空文件夹内的邮件映射。

        Args:
            mailbox_id: 文件夹ID。

        Returns:
            删除的记录数量。
        """
        async with self._db_manager.get_session() as session:
            result = await session.execute(
                delete(MailboxMessageEntity).where(
                    MailboxMessageEntity.mailbox_id == mailbox_id
                )
            )
            await session.flush()
            deleted = result.rowcount or 0

            self._crud_logger.log_delete(
                "清空文件夹邮件",
                {"mailbox_id": mailbox_id, "deleted": deleted},
            )

            return deleted
