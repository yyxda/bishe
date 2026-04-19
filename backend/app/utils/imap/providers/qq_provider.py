"""QQ邮箱服务商提供者。

QQ邮箱使用标准IMAP协议，无需特殊处理。
支持SSL连接，端口993(IMAP)/465(SMTP)。
"""

from logging import Logger
from typing import Optional

from app.utils.imap.providers.base_provider import BaseEmailProvider, ProviderConfig


class QQEmailProvider(BaseEmailProvider):
    """QQ邮箱服务商提供者。

    QQ邮箱遵循标准IMAP协议，不需要发送ID命令或其他特殊处理。

    服务器配置：
        - IMAP: imap.qq.com:993 (SSL)
        - SMTP: smtp.qq.com:465 (SSL)

    认证方式：
        - 需要使用授权码而非邮箱密码
        - 授权码在QQ邮箱设置中生成

    特殊文件夹（UTF-7编码）：
        - 收件箱: INBOX
        - 已发送: Sent Messages
        - 草稿箱: Drafts
        - 已删除: Deleted Messages
        - 垃圾邮件: Junk
    """

    def __init__(self, logger: Optional[Logger] = None):
        """初始化QQ邮箱提供者。

        Args:
            logger: 日志记录器。
        """
        super().__init__(logger)

    @property
    def name(self) -> str:
        """服务商名称。

        Returns:
            QQ邮箱的可读名称。
        """
        return "QQ邮箱"

    @property
    def default_config(self) -> ProviderConfig:
        """QQ邮箱默认配置。

        Returns:
            QQ邮箱的IMAP/SMTP服务器配置。
        """
        return ProviderConfig(
            imap_host="imap.qq.com",
            imap_port=993,
            smtp_host="smtp.qq.com",
            smtp_port=465,
            use_ssl=True,
        )

    def requires_id_command(self) -> bool:
        """QQ邮箱不强制要求ID命令。

        Returns:
            False，表示不需要发送ID命令。
        """
        return False

    def get_special_folders(self) -> dict[str, str]:
        """QQ邮箱特殊文件夹映射。

        Returns:
            QQ邮箱的特殊文件夹名称映射。
        """
        return {
            "inbox": "INBOX",
            "sent": "Sent Messages",
            "drafts": "Drafts",
            "trash": "Deleted Messages",
            "junk": "Junk",
        }
