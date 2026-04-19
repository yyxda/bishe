"""发件人白名单规则实体定义。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SenderWhitelistEntity(Base):
    """发件人白名单规则实体ORM模型。

    映射到数据库的sender_whitelist表，存储发件人白名单规则。

    Attributes:
        id: 主键ID。
        rule_type: 规则类型（EMAIL/DOMAIN/DOMAIN-SUFFIX/DOMAIN-KEYWORD）。
        rule_value: 规则值。
        description: 规则描述。
        is_active: 是否启用。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "sender_whitelist"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="用户ID（NULL表示全局白名单）"
    )
    rule_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="规则类型"
    )
    rule_value: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="规则值"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="规则描述"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, server_default="1", comment="是否启用"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def __repr__(self) -> str:
        """返回发件人白名单规则的字符串表示。

        Returns:
            发件人白名单规则的调试字符串。
        """
        return f"<SenderWhitelistEntity(id={self.id}, type={self.rule_type}, value={self.rule_value})>"