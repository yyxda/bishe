"""邮箱密码加密工具模块。"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PasswordEncryptor:
    """邮箱密码加密器。

    使用Fernet对称加密算法加密和解密邮箱授权密码。
    密钥通过PBKDF2从主密钥派生。
    """

    def __init__(self, master_key: Optional[str] = None) -> None:
        """初始化密码加密器。

        Args:
            master_key: 主密钥字符串。如果不提供，则使用默认密钥。
                生产环境应该从环境变量读取。
        """
        # 使用固定盐值（实际生产中应该为每个密码生成随机盐值并存储）
        self._salt = b"argus_email_salt_v1"
        self._master_key = (master_key or "argus_default_master_key_2024").encode()
        self._fernet = self._create_fernet()

    def _create_fernet(self) -> Fernet:
        """创建Fernet加密器实例。

        Returns:
            配置好的Fernet加密器。
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key))
        return Fernet(key)

    def encrypt(self, plain_password: str) -> str:
        """加密密码。

        Args:
            plain_password: 明文密码。

        Returns:
            Base64编码的加密密码字符串。
        """
        if not plain_password:
            return ""
        encrypted = self._fernet.encrypt(plain_password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_password: str) -> str:
        """解密密码。

        Args:
            encrypted_password: 加密后的密码字符串。

        Returns:
            解密后的明文密码。

        Raises:
            Exception: 解密失败时抛出异常。
        """
        if not encrypted_password:
            return ""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"密码解密失败: {e}") from e
