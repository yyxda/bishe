"""IMAP邮箱配置模块。

提供QQ邮箱、网易163邮箱等常用邮箱的默认配置。
"""

from dataclasses import dataclass
from typing import Optional

from app.entities.email_account_entity import EmailType


@dataclass(frozen=True)
class ImapConfig:
    """IMAP/SMTP邮箱配置。

    Attributes:
        imap_host: IMAP服务器地址。
        imap_port: IMAP端口。
        smtp_host: SMTP服务器地址。
        smtp_port: SMTP端口。
        use_ssl: 是否使用SSL。
    """

    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    use_ssl: bool = True


# QQ邮箱默认配置
QQ_IMAP_CONFIG = ImapConfig(
    imap_host="imap.qq.com",
    imap_port=993,
    smtp_host="smtp.qq.com",
    smtp_port=465,
    use_ssl=True,
)

# 网易163邮箱默认配置
NETEASE_IMAP_CONFIG = ImapConfig(
    imap_host="imap.163.com",
    imap_port=993,
    smtp_host="smtp.163.com",
    smtp_port=465,
    use_ssl=True,
)

# 学校默认邮箱配置（假设使用标准配置）
DEFAULT_SCHOOL_CONFIG = ImapConfig(
    imap_host="mail.hhstu.edu.cn",
    imap_port=993,
    smtp_host="mail.hhstu.edu.cn",
    smtp_port=465,
    use_ssl=True,
)


class ImapConfigFactory:
    """IMAP配置工厂类。

    根据邮箱类型返回对应的默认配置。
    """

    # 邮箱类型与配置的映射
    _CONFIG_MAP = {
        EmailType.QQ: QQ_IMAP_CONFIG,
        EmailType.NETEASE: NETEASE_IMAP_CONFIG,
        EmailType.DEFAULT: DEFAULT_SCHOOL_CONFIG,
    }

    @classmethod
    def get_config(cls, email_type: EmailType) -> Optional[ImapConfig]:
        """获取指定邮箱类型的默认配置。

        Args:
            email_type: 邮箱类型。

        Returns:
            IMAP配置，如果是自定义类型则返回None。
        """
        return cls._CONFIG_MAP.get(email_type)

    @classmethod
    def get_config_or_default(
        cls,
        email_type: EmailType,
        imap_host: Optional[str] = None,
        imap_port: Optional[int] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        use_ssl: Optional[bool] = None,
    ) -> ImapConfig:
        """获取配置，优先使用自定义值，否则使用默认配置。

        Args:
            email_type: 邮箱类型。
            imap_host: 自定义IMAP服务器地址。
            imap_port: 自定义IMAP端口。
            smtp_host: 自定义SMTP服务器地址。
            smtp_port: 自定义SMTP端口。
            use_ssl: 自定义是否使用SSL。

        Returns:
            合并后的IMAP配置。
        """
        default_config = cls.get_config(email_type)

        if default_config:
            return ImapConfig(
                imap_host=imap_host or default_config.imap_host,
                imap_port=imap_port or default_config.imap_port,
                smtp_host=smtp_host or default_config.smtp_host,
                smtp_port=smtp_port or default_config.smtp_port,
                use_ssl=use_ssl if use_ssl is not None else default_config.use_ssl,
            )

        # 自定义类型必须提供所有配置
        if not all([imap_host, smtp_host]):
            raise ValueError("自定义邮箱类型必须提供IMAP和SMTP服务器地址")

        return ImapConfig(
            imap_host=imap_host,
            imap_port=imap_port or 993,
            smtp_host=smtp_host,
            smtp_port=smtp_port or 465,
            use_ssl=use_ssl if use_ssl is not None else True,
        )
