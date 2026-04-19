"""用户实体定义。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserEntity(Base):
    """用户实体ORM模型。

    映射到数据库的users表，存储用户基本信息。

    Attributes:
        id: 主键ID。
        student_id: 学号，唯一标识。
        password_hash: 密码哈希值。
        display_name: 用户显示名称。
        is_active: 是否启用账号。
        role: 用户角色（user/admin）。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    student_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True, comment="学号"
    )
    password_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="密码哈希"
    )
    display_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="显示名称"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, server_default="1", comment="是否启用"
    )
    role: Mapped[str] = mapped_column(
        String(20), default="user", server_default="user", comment="用户角色"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="邮箱地址"
    )
    email_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="邮箱类型: qq, 163, netease等"
    )
    auth_code: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="授权码"
    )

    def __repr__(self) -> str:
        """返回用户实体的字符串表示。

        Returns:
            用户实体的调试字符串。
        """
        return f"<UserEntity(id={self.id}, student_id={self.student_id})>"