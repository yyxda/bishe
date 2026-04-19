"""系统设置实体定义。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SystemSettingsEntity(Base):
    """系统设置实体ORM模型。

    映射到数据库的system_settings表，存储全局系统设置。

    Attributes:
        id: 主键ID。
        enable_long_url_detection: 是否启用长链接检测。
        enable_rule_based_detection: 是否启用规则检测（BERT + 规则混合检测）。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    enable_long_url_detection: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用长链接检测"
    )
    enable_rule_based_detection: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否启用规则检测（BERT + 规则混合检测）"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def __repr__(self) -> str:
        """返回系统设置的字符串表示。

        Returns:
            系统设置的调试字符串。
        """
        return (
            f"<SystemSettingsEntity(id={self.id}, "
            f"enable_long_url_detection={self.enable_long_url_detection}, "
            f"enable_rule_based_detection={self.enable_rule_based_detection})>"
        )