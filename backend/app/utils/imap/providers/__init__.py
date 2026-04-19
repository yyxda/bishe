"""邮箱服务商提供者模块。

该模块采用策略模式，为不同的邮箱服务商（QQ、网易、Gmail等）提供统一的接口，
同时允许各服务商实现自己的特定逻辑。

使用示例：
    from app.utils.imap.providers import ProviderFactory, EmailType

    # 获取对应的服务商提供者
    provider = ProviderFactory.get_provider(EmailType.NETEASE)

    # 使用提供者
    await provider.post_login_hook(imap_client)
"""

from app.utils.imap.providers.base_provider import BaseEmailProvider
from app.utils.imap.providers.qq_provider import QQEmailProvider
from app.utils.imap.providers.netease_provider import NeteaseEmailProvider
from app.utils.imap.providers.default_provider import DefaultEmailProvider
from app.utils.imap.providers.provider_factory import ProviderFactory

__all__ = [
    "BaseEmailProvider",
    "QQEmailProvider",
    "NeteaseEmailProvider",
    "DefaultEmailProvider",
    "ProviderFactory",
]
