"""密码哈希工具。"""

import hashlib


class PasswordHasher:
    """密码哈希与校验工具类。

    该工具类用于将明文密码转换为不可逆的哈希值，并用于密码校验。
    """

    def hash(self, raw_password: str) -> str:
        """对明文密码进行哈希处理。

        Args:
            raw_password: 明文密码。

        Returns:
            哈希后的密码字符串。
        """
        return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        """校验明文密码是否匹配哈希值。

        Args:
            raw_password: 明文密码。
            hashed_password: 哈希后的密码。

        Returns:
            密码是否匹配。
        """
        return self.hash(raw_password) == hashed_password
