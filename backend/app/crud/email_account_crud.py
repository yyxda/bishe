"""邮箱账户数据访问层。"""

from typing import List, Optional

from sqlalchemy import select

from app.core.database import DatabaseManager
from app.entities.email_account_entity import EmailAccountEntity, EmailType
from app.utils.logging.crud_logger import CrudLogger
from app.utils.crypto.password_encryptor import PasswordEncryptor


class EmailAccountCrud:
    """邮箱账户CRUD操作类。

    提供邮箱账户数据的增删改查操作。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        password_encryptor: PasswordEncryptor,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化邮箱账户CRUD。

        Args:
            db_manager: 数据库管理器实例。
            password_encryptor: 密码加密器。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._password_encryptor = password_encryptor
        self._crud_logger = crud_logger

    async def get_by_user_id(self, user_id: int) -> List[EmailAccountEntity]:
        """获取用户的所有邮箱账户。

        Args:
            user_id: 用户ID。

        Returns:
            邮箱账户实体列表。
        """
        async with self._db_manager.get_session() as session:
            query = (
                select(EmailAccountEntity)
                .where(EmailAccountEntity.user_id == user_id)
                .where(EmailAccountEntity.is_active == True)
            )
            result = await session.execute(query)
            accounts = result.scalars().all()

            self._crud_logger.log_read(
                "查询用户邮箱账户",
                {"user_id": user_id, "count": len(accounts)},
            )

            return list(accounts)

    async def get_by_id(self, account_id: int) -> Optional[EmailAccountEntity]:
        """根据ID获取邮箱账户。

        Args:
            account_id: 邮箱账户ID。

        Returns:
            邮箱账户实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(EmailAccountEntity).where(
                EmailAccountEntity.id == account_id
            )
            result = await session.execute(query)
            account = result.scalar_one_or_none()

            if account:
                self._crud_logger.log_read(
                    "查询到邮箱账户",
                    {"account_id": account_id, "found": True},
                )
            else:
                self._crud_logger.log_read(
                    "未查询到邮箱账户",
                    {"account_id": account_id, "found": False},
                )

            return account

    async def get_by_email_address(
        self, user_id: int, email_address: str
    ) -> Optional[EmailAccountEntity]:
        """根据邮箱地址获取账户。

        Args:
            user_id: 用户ID。
            email_address: 邮箱地址。

        Returns:
            邮箱账户实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(EmailAccountEntity).where(
                EmailAccountEntity.user_id == user_id,
                EmailAccountEntity.email_address == email_address,
                EmailAccountEntity.is_active == True,  # 只查询激活的账户
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        email_address: str,
        email_type: EmailType,
        auth_password: str,
        imap_host: Optional[str] = None,
        imap_port: int = 993,
        smtp_host: Optional[str] = None,
        smtp_port: int = 465,
        use_ssl: bool = True,
        auth_user: Optional[str] = None,
    ) -> EmailAccountEntity:
        """创建邮箱账户。

        Args:
            user_id: 用户ID。
            email_address: 邮箱地址。
            email_type: 邮箱类型。
            auth_password: 授权密码（明文）。
            imap_host: IMAP服务器地址。
            imap_port: IMAP端口。
            smtp_host: SMTP服务器地址。
            smtp_port: SMTP端口。
            use_ssl: 是否使用SSL。
            auth_user: 认证用户名。

        Returns:
            创建的邮箱账户实体。
        """
        async with self._db_manager.get_session() as session:
            # 加密密码
            encrypted_password = self._password_encryptor.encrypt(auth_password)

            account = EmailAccountEntity(
                user_id=user_id,
                email_address=email_address,
                email_type=email_type,
                imap_host=imap_host,
                imap_port=imap_port,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                use_ssl=use_ssl,
                auth_user=auth_user or email_address,
                auth_password_encrypted=encrypted_password,
            )
            session.add(account)
            await session.flush()
            await session.refresh(account)

            self._crud_logger.log_create(
                "创建邮箱账户",
                {
                    "user_id": user_id,
                    "email_address": email_address,
                    "email_type": email_type.value,
                },
            )

            return account

    async def update_last_sync(self, account_id: int) -> bool:
        """更新邮箱账户的最后同步时间。

        Args:
            account_id: 邮箱账户ID。

        Returns:
            是否更新成功。
        """
        from datetime import datetime

        async with self._db_manager.get_session() as session:
            query = select(EmailAccountEntity).where(
                EmailAccountEntity.id == account_id
            )
            result = await session.execute(query)
            account = result.scalar_one_or_none()

            if not account:
                return False

            account.last_sync_at = datetime.now()
            await session.flush()

            self._crud_logger.log_update(
                "更新邮箱同步时间",
                {"account_id": account_id},
            )

            return True

    async def delete(self, account_id: int) -> bool:
        """删除邮箱账户（硬删除）。

        会级联删除所有关联的数据：
        - 邮箱文件夹（mailboxes）
        - 邮件元数据（email_messages）
        - 邮件正文（email_bodies）
        - 邮件收件人（email_recipients）
        - 邮箱-邮件映射（mailbox_messages）

        Args:
            account_id: 邮箱账户ID。

        Returns:
            是否删除成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(EmailAccountEntity).where(
                EmailAccountEntity.id == account_id
            )
            result = await session.execute(query)
            account = result.scalar_one_or_none()

            if not account:
                return False

            # 记录删除的邮箱地址用于日志
            email_address = account.email_address

            # 硬删除：依赖数据库的级联删除清空所有关联数据
            await session.delete(account)
            await session.flush()

            self._crud_logger.log_delete(
                "硬删除邮箱账户及所有关联数据",
                {
                    "account_id": account_id,
                    "email_address": email_address,
                },
            )

            return True

    def decrypt_password(self, encrypted_password: str) -> str:
        """解密邮箱密码。

        Args:
            encrypted_password: 加密后的密码。

        Returns:
            解密后的明文密码。
        """
        return self._password_encryptor.decrypt(encrypted_password)
