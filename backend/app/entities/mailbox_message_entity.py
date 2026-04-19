"""邮箱文件夹邮件实体定义。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MailboxMessageEntity(Base):
    """邮箱文件夹邮件ORM模型。

    映射到数据库的mailbox_messages表，记录邮件在具体文件夹中的UID与状态。

    Attributes:
        id: 主键ID。
        mailbox_id: 关联的邮箱文件夹ID。
        message_id: 关联的邮件元数据ID。
        uid: IMAP UID。
        flags: IMAP标志位原始字符串。
        is_read: 是否已读。
        is_flagged: 是否标星。
        is_answered: 是否已回复。
        is_deleted: 是否删除。
        is_draft: 是否草稿。
        internal_date: IMAP内部接收时间。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "mailbox_messages"
    __table_args__ = (
        UniqueConstraint("mailbox_id", "uid", name="uq_mailbox_uid"),
        Index("ix_mailbox_internal_date", "mailbox_id", "internal_date"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    mailbox_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("mailboxes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="邮箱文件夹ID",
    )
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("email_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="邮件元数据ID",
    )
    uid: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="IMAP UID"
    )
    flags: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="IMAP标志位"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已读")
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否标星")
    is_answered: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否已回复"
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否删除")
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否草稿")
    internal_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="内部日期"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    mailbox = relationship("MailboxEntity", back_populates="mailbox_messages")
    message = relationship("EmailEntity", back_populates="mailbox_messages")

    def __repr__(self) -> str:
        """返回邮箱文件夹邮件实体的字符串表示。

        Returns:
            邮箱文件夹邮件实体的调试字符串。
        """
        return (
            "<MailboxMessageEntity(id="
            f"{self.id}, mailbox_id={self.mailbox_id}, uid={self.uid})>"
        )
