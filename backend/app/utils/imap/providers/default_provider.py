"""默认邮箱服务商提供者。

用于处理未知或自定义邮箱服务商，提供标准IMAP协议支持。
"""

from logging import Logger
from typing import Optional

from app.utils.imap.providers.base_provider import BaseEmailProvider, ProviderConfig


class DefaultEmailProvider(BaseEmailProvider):
    """默认邮箱服务商提供者。

    用于处理学校邮箱、企业邮箱或其他未特别适配的邮箱服务商。
    使用标准IMAP协议，不做特殊处理。

    此类可作为新增邮箱服务商的模板。
    """

    def __init__(
        self,
        logger: Optional[Logger] = None,
        imap_host: str = "mail.example.com",
        imap_port: int = 993,
        smtp_host: str = "mail.example.com",
        smtp_port: int = 465,
        use_ssl: bool = True,
        provider_name: str = "默认邮箱",
    ):
        """初始化默认邮箱提供者。

        Args:
            logger: 日志记录器。
            imap_host: IMAP服务器地址。
            imap_port: IMAP端口。
            smtp_host: SMTP服务器地址。
            smtp_port: SMTP端口。
            use_ssl: 是否使用SSL。
            provider_name: 服务商名称。
        """
        super().__init__(logger)
        self._imap_host = imap_host
        self._imap_port = imap_port
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._use_ssl = use_ssl
        self._provider_name = provider_name

    @property
    def name(self) -> str:
        """服务商名称。

        Returns:
            配置的服务商名称。
        """
        return self._provider_name

    @property
    def default_config(self) -> ProviderConfig:
        """默认配置。

        Returns:
            根据初始化参数构建的配置。
        """
        return ProviderConfig(
            imap_host=self._imap_host,
            imap_port=self._imap_port,
            smtp_host=self._smtp_host,
            smtp_port=self._smtp_port,
            use_ssl=self._use_ssl,
        )


class SchoolEmailProvider(DefaultEmailProvider):
    """学校邮箱服务商提供者。

    适用于学校教育邮箱（如 xxx@hhstu.edu.cn）。
    """

    def __init__(self, logger: Optional[Logger] = None):
        """初始化学校邮箱提供者。

        Args:
            logger: 日志记录器。
        """
        super().__init__(
            logger=logger,
            imap_host="mail.hhstu.edu.cn",
            imap_port=993,
            smtp_host="mail.hhstu.edu.cn",
            smtp_port=465,
            use_ssl=True,
            provider_name="学校邮箱",
        )
