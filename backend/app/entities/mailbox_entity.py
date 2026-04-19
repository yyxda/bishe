"""邮箱文件夹实体定义。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MailboxEntity(Base):
    """邮箱文件夹ORM模型。

    映射到数据库的mailboxes表，用于存储邮箱文件夹信息与同步游标。

    Attributes:
        id: 主键ID。
        email_account_id: 关联的邮箱账户ID。
        name: 文件夹名称（例如INBOX）。
        delimiter: IMAP层级分隔符。
        attributes: 文件夹属性（原始字符串）。
        uid_validity: UID有效期标识。
        last_uid: 最后同步的UID游标。
        last_sync_at: 最后同步时间。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "mailboxes"
    __table_args__ = (
        UniqueConstraint(
            "email_account_id",
            "name",
            name="uq_mailbox_account_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    email_account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("email_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="邮箱账户ID",
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="文件夹名称"
    )
    delimiter: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="层级分隔符"
    )
    attributes: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="文件夹属性"
    )
    uid_validity: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="UID有效期"
    )
    last_uid: Mapped[int] = mapped_column(
        BigInteger, default=0, comment="最后同步UID"
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="最后同步时间"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    account = relationship("EmailAccountEntity", back_populates="mailboxes")
    mailbox_messages = relationship(
        "MailboxMessageEntity",
        back_populates="mailbox",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """返回邮箱文件夹实体的字符串表示。

        Returns:
            邮箱文件夹实体的调试字符串。
        """
        return f"<MailboxEntity(id={self.id}, name={self.name})>"
