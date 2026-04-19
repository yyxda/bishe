"""邮件元数据实体定义。"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PhishingLevel(str, Enum):
    """钓鱼邮件危险等级枚举。

    Attributes:
        NORMAL: 正常邮件。
        SUSPICIOUS: 疑似钓鱼邮件。
        HIGH_RISK: 高危钓鱼邮件。
    """

    NORMAL = "NORMAL"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"


class PhishingStatus(str, Enum):
    """钓鱼检测状态枚举。

    Attributes:
        PENDING: 检测中。
        COMPLETED: 检测完成。
        FAILED: 检测失败。
    """

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EmailEntity(Base):
    """邮件元数据ORM模型。

    映射到数据库的email_messages表，存储邮件的元信息与钓鱼检测结果。
    大字段正文拆分到独立表，以降低列表查询的IO开销。

    Attributes:
        id: 主键ID。
        email_account_id: 关联的邮箱账户ID。
        message_id: 邮件唯一标识（Message-ID）。
        subject: 邮件主题。
        sender_name: 发件人姓名。
        sender_address: 发件人邮箱。
        snippet: 列表摘要。
        received_at: 接收时间（用于列表排序）。
        size: 邮件大小。
        phishing_level: 钓鱼危险等级。
        phishing_score: 钓鱼评分（0-1）。
        phishing_reason: 钓鱼判定原因。
        phishing_status: 钓鱼检测状态。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "email_messages"
    __table_args__ = (
        UniqueConstraint(
            "email_account_id",
            "message_id",
            name="uq_email_account_message_id",
        ),
        Index("ix_email_account_received_at", "email_account_id", "received_at"),
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
    message_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="邮件唯一标识"
    )
    subject: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="邮件主题"
    )
    sender_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="发件人姓名"
    )
    sender_address: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="发件人邮箱"
    )
    snippet: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="邮件摘要"
    )
    received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True, comment="接收时间"
    )
    size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="邮件大小"
    )
    phishing_level: Mapped[PhishingLevel] = mapped_column(
        SQLEnum(PhishingLevel),
        default=PhishingLevel.NORMAL,
        comment="钓鱼危险等级",
    )
    phishing_score: Mapped[float] = mapped_column(default=0.0, comment="钓鱼评分")
    phishing_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="钓鱼判定原因"
    )
    phishing_status: Mapped[PhishingStatus] = mapped_column(
        SQLEnum(PhishingStatus),
        default=PhishingStatus.COMPLETED,
        nullable=False,
        comment="钓鱼检测状态",
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    email_account = relationship("EmailAccountEntity", back_populates="email_messages")
    body = relationship(
        "EmailBodyEntity",
        back_populates="message",
        uselist=False,
        cascade="all, delete-orphan",
    )
    recipients = relationship(
        "EmailRecipientEntity",
        back_populates="message",
        cascade="all, delete-orphan",
    )
    mailbox_messages = relationship(
        "MailboxMessageEntity",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """返回邮件元数据实体的字符串表示。

        Returns:
            邮件元数据的调试字符串。
        """
        return f"<EmailEntity(id={self.id}, subject={self.subject})>"
