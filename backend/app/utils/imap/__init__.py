"""IMAP工具模块。

该模块提供IMAP/SMTP邮件客户端功能，支持多种邮箱服务商。

子模块：
    - providers: 邮箱服务商提供者，采用策略模式支持不同服务商的特定处理
    - imap_client: 异步IMAP客户端
    - smtp_client: 异步SMTP客户端
    - imap_config: 邮箱配置类

使用示例：
    >>> from app.utils.imap import ImapClient
    >>> from app.utils.imap.providers import ProviderFactory
    >>> from app.entities.email_account_entity import EmailType
    >>>
    >>> provider = ProviderFactory.get_provider(EmailType.NETEASE)
    >>> client = ImapClient(provider=provider)
    >>> await client.connect("user@163.com", "password")
"""

from app.utils.imap.imap_config import (
    ImapConfig,
    ImapConfigFactory,
    QQ_IMAP_CONFIG,
    NETEASE_IMAP_CONFIG,
    DEFAULT_SCHOOL_CONFIG,
)
try:
    from app.utils.imap.imap_client import ImapClient
except ModuleNotFoundError:
    # 在测试环境中可缺少IMAP依赖，避免导入失败影响其他模块。
    ImapClient = None

from app.utils.imap.imap_models import (
    MailboxInfo,
    MailboxStatus,
    FetchedEmail,
    ParsedEmail,
)
from app.utils.imap.email_parser import EmailParser
try:
    from app.utils.imap.smtp_client import SmtpClient
except ModuleNotFoundError:
    # 测试环境下缺少SMTP依赖时降级处理。
    SmtpClient = None

__all__ = [
    # 配置类
    "ImapConfig",
    "ImapConfigFactory",
    "QQ_IMAP_CONFIG",
    "NETEASE_IMAP_CONFIG",
    "DEFAULT_SCHOOL_CONFIG",
    # 客户端
    "ImapClient",
    "SmtpClient",
    # 数据模型
    "MailboxInfo",
    "MailboxStatus",
    "FetchedEmail",
    "ParsedEmail",
    # 工具类
    "EmailParser",
]
