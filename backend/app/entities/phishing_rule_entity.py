"""钓鱼检测规则实体定义。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, func, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PhishingRuleEntity(Base):
    """钓鱼检测规则实体ORM模型。

    映射到数据库的phishing_rules表，存储自定义的钓鱼检测规则。

    Attributes:
        id: 主键ID。
        rule_name: 规则名称。
        rule_type: 规则类型（URL/SENDER/CONTENT/STRUCTURE）。
        rule_pattern: 规则模式（正则表达式或关键词）。
        rule_description: 规则描述。
        severity: 规则严重程度（1-10，10为最严重）。
        is_active: 是否启用。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "phishing_rules"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    rule_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="规则名称"
    )
    rule_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="规则类型：URL/SENDER/CONTENT/STRUCTURE"
    )
    rule_pattern: Mapped[str] = mapped_column(
        Text, nullable=False, comment="规则模式（正则表达式或关键词）"
    )
    rule_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="规则描述"
    )
    severity: Mapped[int] = mapped_column(
        Integer, default=5, comment="规则严重程度（1-10）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def __repr__(self) -> str:
        """返回规则的字符串表示。

        Returns:
            规则的调试字符串。
        """
        return (
            f"<PhishingRuleEntity(id={self.id}, "
            f"rule_name={self.rule_name}, "
            f"rule_type={self.rule_type}, "
            f"severity={self.severity}, "
            f"is_active={self.is_active})>"
        )