"""邮箱服务商工厂模块。

使用工厂模式根据邮箱类型创建对应的服务商提供者实例。
支持自动检测邮箱类型和自定义配置。
"""

from logging import Logger
from typing import Optional, Type

from app.entities.email_account_entity import EmailType
from app.utils.imap.providers.base_provider import BaseEmailProvider, ProviderConfig
from app.utils.imap.providers.qq_provider import QQEmailProvider
from app.utils.imap.providers.netease_provider import (
    NeteaseEmailProvider,
    Netease126Provider,
    NeteaseYeahProvider,
)
from app.utils.imap.providers.default_provider import (
    DefaultEmailProvider,
    SchoolEmailProvider,
)


class ProviderFactory:
    """邮箱服务商工厂类。

    负责根据邮箱类型或邮箱地址创建对应的服务商提供者实例。

    使用示例：
        # 根据邮箱类型获取提供者
        provider = ProviderFactory.get_provider(EmailType.QQ)

        # 根据邮箱地址自动检测
        provider = ProviderFactory.get_provider_by_email("test@163.com")

        # 注册新的服务商
        ProviderFactory.register(EmailType.GMAIL, GmailProvider)
    """

    # 邮箱类型到提供者类的映射
    _provider_map: dict[EmailType, Type[BaseEmailProvider]] = {
        EmailType.QQ: QQEmailProvider,
        EmailType.NETEASE: NeteaseEmailProvider,
        EmailType.DEFAULT: SchoolEmailProvider,
    }

    # 邮箱域名到提供者类的映射（用于自动检测）
    _domain_map: dict[str, Type[BaseEmailProvider]] = {
        "qq.com": QQEmailProvider,
        "163.com": NeteaseEmailProvider,
        "126.com": Netease126Provider,
        "yeah.net": NeteaseYeahProvider,
        "hhstu.edu.cn": SchoolEmailProvider,
    }

    @classmethod
    def get_provider(
        cls,
        email_type: EmailType,
        logger: Optional[Logger] = None,
        **custom_config,
    ) -> BaseEmailProvider:
        """根据邮箱类型获取服务商提供者。

        Args:
            email_type: 邮箱类型枚举。
            logger: 日志记录器。
            **custom_config: 自定义配置参数（用于CUSTOM类型）。

        Returns:
            对应的服务商提供者实例。

        Example:
            >>> provider = ProviderFactory.get_provider(EmailType.QQ)
            >>> print(provider.name)
            'QQ邮箱'
        """
        provider_class = cls._provider_map.get(email_type)

        if provider_class:
            return provider_class(logger=logger)

        # 自定义类型，使用DefaultEmailProvider
        if email_type == EmailType.CUSTOM:
            return DefaultEmailProvider(
                logger=logger,
                imap_host=custom_config.get("imap_host", ""),
                imap_port=custom_config.get("imap_port", 993),
                smtp_host=custom_config.get("smtp_host", ""),
                smtp_port=custom_config.get("smtp_port", 465),
                use_ssl=custom_config.get("use_ssl", True),
                provider_name="自定义邮箱",
            )

        # 未知类型，返回默认提供者
        return DefaultEmailProvider(logger=logger)

    @classmethod
    def get_provider_by_email(
        cls,
        email_address: str,
        logger: Optional[Logger] = None,
    ) -> BaseEmailProvider:
        """根据邮箱地址自动检测并获取服务商提供者。

        通过分析邮箱地址的域名部分，自动识别邮箱服务商。

        Args:
            email_address: 邮箱地址。
            logger: 日志记录器。

        Returns:
            检测到的服务商提供者实例。

        Example:
            >>> provider = ProviderFactory.get_provider_by_email("test@163.com")
            >>> print(provider.name)
            '网易163邮箱'
        """
        if "@" not in email_address:
            return DefaultEmailProvider(logger=logger)

        domain = email_address.split("@")[1].lower()

        provider_class = cls._domain_map.get(domain)
        if provider_class:
            return provider_class(logger=logger)

        # 未知域名，返回默认提供者
        return DefaultEmailProvider(
            logger=logger,
            provider_name=f"未知邮箱({domain})",
        )

    @classmethod
    def register(
        cls,
        email_type: EmailType,
        provider_class: Type[BaseEmailProvider],
        domains: Optional[list[str]] = None,
    ) -> None:
        """注册新的邮箱服务商。

        允许在运行时动态添加新的邮箱服务商支持。

        Args:
            email_type: 邮箱类型枚举。
            provider_class: 服务商提供者类。
            domains: 关联的邮箱域名列表。

        Example:
            >>> class GmailProvider(BaseEmailProvider):
            ...     pass
            >>> ProviderFactory.register(
            ...     EmailType.GMAIL,
            ...     GmailProvider,
            ...     domains=["gmail.com", "googlemail.com"]
            ... )
        """
        cls._provider_map[email_type] = provider_class

        if domains:
            for domain in domains:
                cls._domain_map[domain.lower()] = provider_class

    @classmethod
    def register_domain(
        cls,
        domain: str,
        provider_class: Type[BaseEmailProvider],
    ) -> None:
        """注册邮箱域名映射。

        Args:
            domain: 邮箱域名。
            provider_class: 服务商提供者类。
        """
        cls._domain_map[domain.lower()] = provider_class

    @classmethod
    def get_supported_types(cls) -> list[EmailType]:
        """获取支持的邮箱类型列表。

        Returns:
            已注册的邮箱类型列表。
        """
        return list(cls._provider_map.keys())

    @classmethod
    def get_supported_domains(cls) -> list[str]:
        """获取支持的邮箱域名列表。

        Returns:
            已注册的邮箱域名列表。
        """
        return list(cls._domain_map.keys())

    @classmethod
    def get_config(
        cls,
        email_type: EmailType,
        **overrides,
    ) -> ProviderConfig:
        """获取邮箱类型的配置。

        Args:
            email_type: 邮箱类型。
            **overrides: 要覆盖的配置项。

        Returns:
            合并后的配置对象。
        """
        provider = cls.get_provider(email_type)
        default = provider.default_config

        return ProviderConfig(
            imap_host=overrides.get("imap_host") or default.imap_host,
            imap_port=overrides.get("imap_port") or default.imap_port,
            smtp_host=overrides.get("smtp_host") or default.smtp_host,
            smtp_port=overrides.get("smtp_port") or default.smtp_port,
            use_ssl=overrides.get("use_ssl") if "use_ssl" in overrides else default.use_ssl,
        )
