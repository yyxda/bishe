"""邮件收件人实体定义。"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecipientType(str, Enum):
    """收件人类型枚举。

    Attributes:
        TO: 收件人。
        CC: 抄送。
        BCC: 密送。
        REPLY_TO: 回复地址。
    """

    TO = "TO"
    CC = "CC"
    BCC = "BCC"
    REPLY_TO = "REPLY_TO"


class EmailRecipientEntity(Base):
    """邮件收件人ORM模型。

    映射到数据库的email_recipients表，存储邮件收件人信息。

    Attributes:
        id: 主键ID。
        message_id: 关联的邮件元数据ID。
        recipient_type: 收件人类型。
        display_name: 显示名称。
        email_address: 邮箱地址。
        created_at: 创建时间。
    """

    __tablename__ = "email_recipients"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("email_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="邮件元数据ID",
    )
    recipient_type: Mapped[RecipientType] = mapped_column(
        SQLEnum(RecipientType), nullable=False, comment="收件人类型"
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="显示名称"
    )
    email_address: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="邮箱地址"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    # 关联关系
    message = relationship("EmailEntity", back_populates="recipients")

    def __repr__(self) -> str:
        """返回收件人实体的字符串表示。

        Returns:
            收件人实体的调试字符串。
        """
        return (
            "<EmailRecipientEntity(id="
            f"{self.id}, email={self.email_address}, type={self.recipient_type})>"
        )
