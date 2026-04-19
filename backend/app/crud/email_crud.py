"""邮件查询数据访问层。"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import selectinload

from app.core.database import DatabaseManager
from app.entities.email_entity import EmailEntity, PhishingLevel, PhishingStatus
from app.entities.mailbox_message_entity import MailboxMessageEntity
from app.utils.logging.crud_logger import CrudLogger


class EmailCrud:
    """邮件查询CRUD操作类。

    提供邮件列表与详情的查询操作，支持游标分页优化。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化邮件CRUD。

        Args:
            db_manager: 数据库管理器实例。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._crud_logger = crud_logger

    async def get_by_mailbox_ids(
        self,
        mailbox_ids: List[int],
        limit: int = 1000,
        offset: int = 0,
    ) -> List[MailboxMessageEntity]:
        """按文件夹获取邮件列表（兼容旧接口）。

        Args:
            mailbox_ids: 文件夹ID列表。
            limit: 返回数量限制。
            offset: 偏移量。

        Returns:
            邮箱文件夹邮件实体列表。
        """
        if not mailbox_ids:
            return []

        async with self._db_manager.get_session() as session:
            query = (
                select(MailboxMessageEntity)
                .where(MailboxMessageEntity.mailbox_id.in_(mailbox_ids))
                .options(selectinload(MailboxMessageEntity.message))
                .order_by(desc(MailboxMessageEntity.internal_date))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            mailbox_messages = result.scalars().all()

            self._crud_logger.log_read(
                "查询邮件列表",
                {"mailbox_ids": mailbox_ids, "count": len(mailbox_messages)},
            )

            return list(mailbox_messages)

    async def get_by_mailbox_ids_cursor(
        self,
        mailbox_ids: List[int],
        limit: int = 1000,
        cursor_date: Optional[datetime] = None,
        cursor_id: Optional[int] = None,
    ) -> Tuple[List[MailboxMessageEntity], Optional[str]]:
        """按文件夹获取邮件列表（游标分页优化版）。

        使用游标分页替代OFFSET，提高大数据集查询性能。
        游标基于internal_date和id组合，确保唯一性和稳定排序。

        Args:
            mailbox_ids: 文件夹ID列表。
            limit: 返回数量限制。
            cursor_date: 游标日期（上一页最后一条的internal_date）。
            cursor_id: 游标ID（上一页最后一条的id）。

        Returns:
            元组(邮件列表, 下一页游标字符串)。
            游标字符串格式: "timestamp_id"，如 "1704067200000_123"
        """
        if not mailbox_ids:
            return [], None

        async with self._db_manager.get_session() as session:
            # 构建基础查询
            base_query = (
                select(MailboxMessageEntity)
                .where(MailboxMessageEntity.mailbox_id.in_(mailbox_ids))
                .options(selectinload(MailboxMessageEntity.message))
            )

            # 如果有游标，添加游标条件
            if cursor_date is not None and cursor_id is not None:
                # 使用(date, id)组合作为游标，处理相同时间戳的情况
                cursor_condition = and_(
                    MailboxMessageEntity.internal_date <= cursor_date,
                    # 排除已经获取的记录
                    ~and_(
                        MailboxMessageEntity.internal_date == cursor_date,
                        MailboxMessageEntity.id >= cursor_id,
                    ),
                )
                base_query = base_query.where(cursor_condition)

            # 添加排序和限制
            query = base_query.order_by(
                desc(MailboxMessageEntity.internal_date),
                desc(MailboxMessageEntity.id),
            ).limit(
                limit + 1
            )  # 多取一条判断是否有下一页

            result = await session.execute(query)
            mailbox_messages = result.scalars().all()
            messages_list = list(mailbox_messages)

            # 判断是否有下一页，生成游标
            next_cursor = None
            if len(messages_list) > limit:
                # 有下一页，截取limit条
                messages_list = messages_list[:limit]
                last_item = messages_list[-1]
                # 生成游标字符串
                if last_item.internal_date:
                    timestamp_ms = int(last_item.internal_date.timestamp() * 1000)
                    next_cursor = f"{timestamp_ms}_{last_item.id}"

            self._crud_logger.log_read(
                "游标分页查询邮件列表",
                {
                    "mailbox_ids": mailbox_ids,
                    "count": len(messages_list),
                    "has_next": next_cursor is not None,
                },
            )

            return messages_list, next_cursor

    async def get_by_id(
        self, mailbox_message_id: int
    ) -> Optional[MailboxMessageEntity]:
        """根据ID获取邮件详情。

        Args:
            mailbox_message_id: 邮箱文件夹邮件ID。

        Returns:
            邮箱文件夹邮件实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = (
                select(MailboxMessageEntity)
                .where(MailboxMessageEntity.id == mailbox_message_id)
                .options(
                    selectinload(MailboxMessageEntity.message).selectinload(
                        EmailEntity.body
                    ),
                    selectinload(MailboxMessageEntity.message).selectinload(
                        EmailEntity.recipients
                    ),
                    selectinload(MailboxMessageEntity.message).selectinload(
                        EmailEntity.email_account
                    ),
                    selectinload(MailboxMessageEntity.mailbox),
                )
            )
            result = await session.execute(query)
            mailbox_message = result.scalar_one_or_none()

            self._crud_logger.log_read(
                "查询邮件详情",
                {
                    "mailbox_message_id": mailbox_message_id,
                    "found": bool(mailbox_message),
                },
            )

            return mailbox_message

    async def mark_as_read(self, mailbox_message_id: int) -> bool:
        """标记邮件为已读。

        Args:
            mailbox_message_id: 邮箱文件夹邮件ID。

        Returns:
            是否标记成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(MailboxMessageEntity).where(
                MailboxMessageEntity.id == mailbox_message_id
            )
            result = await session.execute(query)
            mailbox_message = result.scalar_one_or_none()

            if not mailbox_message:
                return False

            mailbox_message.is_read = True
            await session.flush()

            self._crud_logger.log_update(
                "标记邮件已读",
                {"mailbox_message_id": mailbox_message_id},
            )

            return True

    async def get_count_by_mailbox_ids(
        self,
        mailbox_ids: List[int],
        unread_only: bool = False,
    ) -> int:
        """获取邮件数量（用于统计）。

        Args:
            mailbox_ids: 文件夹ID列表。
            unread_only: 是否只统计未读邮件。

        Returns:
            邮件数量。
        """
        if not mailbox_ids:
            return 0

        from sqlalchemy import func

        async with self._db_manager.get_session() as session:
            query = select(func.count(MailboxMessageEntity.id)).where(
                MailboxMessageEntity.mailbox_id.in_(mailbox_ids)
            )

            if unread_only:
                query = query.where(MailboxMessageEntity.is_read == False)  # noqa: E712

            result = await session.execute(query)
            count = result.scalar() or 0

            return count

    async def update_phishing_result(
        self,
        message_id: int,
        phishing_level: PhishingLevel,
        phishing_score: float,
        phishing_reason: Optional[str] = None,
        phishing_status: PhishingStatus = PhishingStatus.COMPLETED,
    ) -> bool:
        """更新邮件的钓鱼检测结果。

        Args:
            message_id: 邮件消息ID（email_messages表的id）。
            phishing_level: 钓鱼危险等级。
            phishing_score: 钓鱼评分。
            phishing_reason: 钓鱼判定原因。
            phishing_status: 钓鱼检测状态。

        Returns:
            是否更新成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(EmailEntity).where(EmailEntity.id == message_id)
            result = await session.execute(query)
            email_message = result.scalar_one_or_none()

            if not email_message:
                return False

            email_message.phishing_level = phishing_level
            email_message.phishing_score = phishing_score
            email_message.phishing_reason = phishing_reason
            email_message.phishing_status = phishing_status
            await session.flush()

            self._crud_logger.log_update(
                "更新钓鱼检测结果",
                {
                    "message_id": message_id,
                    "phishing_level": phishing_level.value,
                    "phishing_score": phishing_score,
                    "phishing_status": phishing_status.value,
                },
            )

            return True

    async def get_all_email_ids(self) -> List[int]:
        """获取所有邮件的mailbox_message ID（用于重新检测）。

        Returns:
            所有邮件的ID列表。
        """
        async with self._db_manager.get_session() as session:
            query = select(MailboxMessageEntity.id)
            result = await session.execute(query)
            ids = [row[0] for row in result.fetchall()]

            self._crud_logger.log_read(
                "获取所有邮件ID",
                {"count": len(ids)},
            )

            return ids