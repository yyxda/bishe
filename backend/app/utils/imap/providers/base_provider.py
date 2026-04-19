"""邮箱服务商抽象基类。

定义所有邮箱服务商必须实现的接口，确保系统的可扩展性。
新增邮箱服务商时，只需继承此基类并实现相应方法即可。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from aioimaplib import IMAP4_SSL


@dataclass(frozen=True)
class ProviderConfig:
    """邮箱服务商配置。

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


class BaseEmailProvider(ABC):
    """邮箱服务商抽象基类。

    所有邮箱服务商（QQ、网易、Gmail等）都必须继承此类，
    并实现其中的抽象方法和钩子方法。

    设计原则：
        - 开闭原则：对扩展开放，对修改关闭
        - 里氏替换原则：子类可以替换父类使用
        - 依赖倒置原则：依赖抽象而非具体实现

    Attributes:
        name: 服务商名称，用于日志和调试。
        logger: 日志记录器。
    """

    def __init__(self, logger: Optional[Logger] = None):
        """初始化服务商提供者。

        Args:
            logger: 日志记录器，如果未提供则使用默认记录器。
        """
        import logging
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """服务商名称。

        Returns:
            服务商的可读名称，如"QQ邮箱"、"网易163邮箱"。
        """
        pass

    @property
    @abstractmethod
    def default_config(self) -> ProviderConfig:
        """默认服务器配置。

        Returns:
            包含IMAP/SMTP服务器地址和端口的配置对象。
        """
        pass

    async def post_login_hook(self, client: "IMAP4_SSL") -> bool:
        """登录后钩子方法。

        在IMAP登录成功后执行，用于发送服务商特定的命令。
        例如：网易邮箱需要发送ID命令。

        Args:
            client: aioimaplib的IMAP4_SSL客户端实例。

        Returns:
            是否执行成功。即使失败，也不应影响后续操作。
        """
        return True

    async def pre_select_hook(self, client: "IMAP4_SSL", mailbox: str) -> bool:
        """选择文件夹前钩子方法。

        在SELECT命令执行前调用，用于服务商特定的预处理。

        Args:
            client: aioimaplib的IMAP4_SSL客户端实例。
            mailbox: 要选择的文件夹名称。

        Returns:
            是否允许继续执行SELECT。返回False将跳过该文件夹。
        """
        return True

    async def post_select_hook(self, client: "IMAP4_SSL", mailbox: str) -> None:
        """选择文件夹后钩子方法。

        在SELECT命令执行成功后调用。

        Args:
            client: aioimaplib的IMAP4_SSL客户端实例。
            mailbox: 已选择的文件夹名称。
        """
        pass

    def format_mailbox_name(self, mailbox_name: str) -> str:
        """格式化文件夹名称。

        不同服务商可能需要不同的文件夹名称格式。

        Args:
            mailbox_name: 原始文件夹名称。

        Returns:
            格式化后的文件夹名称。
        """
        if not mailbox_name:
            return mailbox_name

        # 默认实现：处理包含空格或引号的名称
        if mailbox_name.startswith('"') and mailbox_name.endswith('"'):
            return mailbox_name

        if " " in mailbox_name or '"' in mailbox_name:
            escaped = mailbox_name.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'

        return mailbox_name

    def get_special_folders(self) -> dict[str, str]:
        """获取特殊文件夹映射。

        不同服务商的特殊文件夹（收件箱、已发送、草稿等）名称可能不同。

        Returns:
            特殊文件夹类型到实际名称的映射字典。
        """
        return {
            "inbox": "INBOX",
            "sent": "Sent",
            "drafts": "Drafts",
            "trash": "Trash",
            "junk": "Junk",
        }

    def requires_id_command(self) -> bool:
        """是否需要发送ID命令。

        某些服务商（如网易）强制要求发送ID命令。

        Returns:
            是否需要发送ID命令。
        """
        return False

    def requires_raw_uid_search(self) -> bool:
        """是否需要使用原始UID SEARCH命令。

        某些服务商不接受SEARCH命令中的CHARSET参数，
        需要使用UID SEARCH <seq-set>的原始命令避免解析错误。

        Returns:
            是否需要使用原始UID SEARCH命令。
        """
        return False

    def get_connection_timeout(self) -> int:
        """获取连接超时时间（秒）。

        不同服务商可能需要不同的超时设置。

        Returns:
            连接超时时间。
        """
        return 30

    def __repr__(self) -> str:
        """返回提供者的字符串表示。

        Returns:
            提供者的调试字符串。
        """
        return f"<{self.__class__.__name__}(name={self.name})>"
