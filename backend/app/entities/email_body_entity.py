"""邮件正文实体定义。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmailBodyEntity(Base):
    """邮件正文ORM模型。

    映射到数据库的email_bodies表，存储大字段正文内容。

    Attributes:
        id: 主键ID。
        message_id: 关联的邮件元数据ID。
        content_text: 纯文本内容。
        content_html: HTML内容。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "email_bodies"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("email_messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="邮件元数据ID",
    )
    content_text: Mapped[Optional[str]] = mapped_column(
        LONGTEXT, nullable=True, comment="纯文本正文"
    )
    content_html: Mapped[Optional[str]] = mapped_column(
        LONGTEXT, nullable=True, comment="HTML正文"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    message = relationship("EmailEntity", back_populates="body")

    def __repr__(self) -> str:
        """返回邮件正文实体的字符串表示。

        Returns:
            邮件正文实体的调试字符串。
        """
        return f"<EmailBodyEntity(id={self.id}, message_id={self.message_id})>"
