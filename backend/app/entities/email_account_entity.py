"""邮箱账户实体定义。"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmailType(str, Enum):
    """邮箱类型枚举。

    Attributes:
        DEFAULT: 学校默认邮箱（学号@hhstu.edu.cn）。
        QQ: QQ邮箱。
        NETEASE: 网易163邮箱。
        CUSTOM: 自定义邮箱配置。
    """

    DEFAULT = "DEFAULT"
    QQ = "QQ"
    NETEASE = "NETEASE"
    CUSTOM = "CUSTOM"


class EmailAccountEntity(Base):
    """邮箱账户实体ORM模型。

    映射到数据库的email_accounts表，存储用户的邮箱账户配置信息。

    Attributes:
        id: 主键ID。
        user_id: 关联的用户ID。
        email_address: 邮箱地址。
        email_type: 邮箱类型。
        imap_host: IMAP服务器地址。
        imap_port: IMAP服务器端口。
        smtp_host: SMTP服务器地址。
        smtp_port: SMTP服务器端口。
        use_ssl: 是否使用SSL连接。
        auth_user: 认证用户名。
        auth_password_encrypted: 加密后的认证密码。
        is_active: 账户是否启用。
        last_sync_at: 最后同步时间。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "email_accounts"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    email_address: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="邮箱地址"
    )
    email_type: Mapped[EmailType] = mapped_column(
        SQLEnum(EmailType), nullable=False, comment="邮箱类型"
    )
    imap_host: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="IMAP服务器"
    )
    imap_port: Mapped[int] = mapped_column(
        BigInteger, default=993, comment="IMAP端口"
    )
    smtp_host: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="SMTP服务器"
    )
    smtp_port: Mapped[int] = mapped_column(
        BigInteger, default=465, comment="SMTP端口"
    )
    use_ssl: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否使用SSL"
    )
    auth_user: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="认证用户名"
    )
    auth_password_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="加密后的密码"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用"
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
    user = relationship("UserEntity", backref="email_accounts")
    mailboxes = relationship(
        "MailboxEntity",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    email_messages = relationship(
        "EmailEntity",
        back_populates="email_account",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """返回邮箱账户实体的字符串表示。

        Returns:
            邮箱账户实体的调试字符串。
        """
        return f"<EmailAccountEntity(id={self.id}, email={self.email_address})>"
