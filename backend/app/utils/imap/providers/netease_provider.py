"""网易邮箱服务商提供者。

网易邮箱（163/126/yeah.net）需要特殊处理：
1. 登录后必须发送ID命令，否则会返回"Unsafe Login"错误
2. ID命令格式需要严格符合RFC 2971规范
"""

from logging import Logger
from typing import Optional, TYPE_CHECKING

from app.utils.imap.providers.base_provider import BaseEmailProvider, ProviderConfig

if TYPE_CHECKING:
    from aioimaplib import IMAP4_SSL


class NeteaseEmailProvider(BaseEmailProvider):
    """网易邮箱服务商提供者。

    网易邮箱（包括163、126、yeah.net等）有特殊的安全机制：
    - 登录后必须发送ID命令标识客户端身份
    - 如果不发送ID命令，SELECT等操作会返回"Unsafe Login"错误

    服务器配置：
        - IMAP: imap.163.com:993 (SSL)
        - SMTP: smtp.163.com:465 (SSL)

    认证方式：
        - 需要使用授权码而非邮箱密码
        - 授权码在网易邮箱设置 -> POP3/SMTP/IMAP 中开启并获取

    特殊文件夹（UTF-7编码）：
        - 收件箱: INBOX
        - 已发送: &XfJT0ZAB- (已发送)
        - 草稿箱: &g0l6P3ux- (草稿箱)
        - 已删除: &XfJSIJZk- (已删除)
        - 垃圾邮件: &V4NXPpCuTvY- (垃圾邮件)
    """

    # 客户端标识信息
    CLIENT_NAME = "Argus"
    CLIENT_VERSION = "1.0"
    CLIENT_VENDOR = "Argus Mail Client"

    def __init__(self, logger: Optional[Logger] = None):
        """初始化网易邮箱提供者。

        Args:
            logger: 日志记录器。
        """
        super().__init__(logger)

    @property
    def name(self) -> str:
        """服务商名称。

        Returns:
            网易邮箱的可读名称。
        """
        return "网易163邮箱"

    @property
    def default_config(self) -> ProviderConfig:
        """网易邮箱默认配置。

        Returns:
            网易邮箱的IMAP/SMTP服务器配置。
        """
        return ProviderConfig(
            imap_host="imap.163.com",
            imap_port=993,
            smtp_host="smtp.163.com",
            smtp_port=465,
            use_ssl=True,
        )

    def requires_id_command(self) -> bool:
        """网易邮箱强制要求ID命令。

        Returns:
            True，表示必须发送ID命令。
        """
        return True

    def requires_raw_uid_search(self) -> bool:
        """网易邮箱需要使用原始UID SEARCH命令。

        网易邮箱的IMAP服务对SEARCH CHARSET utf-8语法不兼容，
        使用原始UID SEARCH可以避免"Parse command error"。

        Returns:
            True，表示需要使用原始UID SEARCH命令。
        """
        return True

    async def post_login_hook(self, client: "IMAP4_SSL") -> bool:
        """登录后发送ID命令。

        网易邮箱要求在登录后发送ID命令来标识客户端，
        否则后续的SELECT等操作会返回"Unsafe Login"错误。

        Args:
            client: aioimaplib的IMAP4_SSL客户端实例。

        Returns:
            ID命令是否执行成功。
        """
        try:
            # 尝试使用协议层发送正确格式的ID命令
            # 网易邮箱要求格式: ID ("name" "value" "version" "value")
            # aioimaplib的id()方法生成的格式 ID ( "name" "value" ) 不被接受
            response = await self._send_id_command_raw(client)

            if response and response.result == "OK":
                self._logger.debug("网易邮箱ID命令发送成功")
                return True
            else:
                self._logger.warning(
                    "网易邮箱ID命令响应异常: %s", response
                )
                # 即使ID命令失败，也尝试继续（某些版本可能不需要）
                return True

        except Exception as exc:
            self._logger.warning("网易邮箱ID命令执行失败: %s", exc)
            # 即使失败也返回True，让后续操作继续尝试
            return True

    async def _send_id_command_raw(self, client: "IMAP4_SSL"):
        """使用原始协议发送ID命令。

        绕过aioimaplib的格式化，直接发送符合163要求的ID命令格式。
        """
        from aioimaplib import Command

        # 构建正确格式的ID参数（不带外层空格）
        id_args = '("name" "Argus" "version" "1.0" "vendor" "ArgusMailClient")'

        try:
            # 使用协议层直接执行命令
            cmd = Command(
                "ID",
                client.protocol.new_tag(),
                id_args,
                loop=client.protocol.loop
            )
            return await client.protocol.execute(cmd)
        except Exception as exc:
            self._logger.debug("原始ID命令发送失败，尝试标准方式: %s", exc)
            # 回退到标准方式
            return await client.id()

    def get_special_folders(self) -> dict[str, str]:
        """网易邮箱特殊文件夹映射。

        网易邮箱的文件夹名称使用UTF-7编码的中文名。

        Returns:
            网易邮箱的特殊文件夹名称映射。
        """
        return {
            "inbox": "INBOX",
            "sent": "&XfJT0ZAB-",      # 已发送
            "drafts": "&g0l6P3ux-",    # 草稿箱
            "trash": "&XfJSIJZk-",     # 已删除
            "junk": "&V4NXPpCuTvY-",   # 垃圾邮件
        }

    def get_connection_timeout(self) -> int:
        """网易邮箱连接超时时间。

        网易邮箱服务器响应可能较慢，适当增加超时时间。

        Returns:
            连接超时时间（秒）。
        """
        return 60


class Netease126Provider(NeteaseEmailProvider):
    """网易126邮箱提供者。

    继承自网易163邮箱提供者，仅修改服务器地址。
    """

    @property
    def name(self) -> str:
        """服务商名称。

        Returns:
            网易126邮箱的可读名称。
        """
        return "网易126邮箱"

    @property
    def default_config(self) -> ProviderConfig:
        """网易126邮箱默认配置。

        Returns:
            网易126邮箱的IMAP/SMTP服务器配置。
        """
        return ProviderConfig(
            imap_host="imap.126.com",
            imap_port=993,
            smtp_host="smtp.126.com",
            smtp_port=465,
            use_ssl=True,
        )


class NeteaseYeahProvider(NeteaseEmailProvider):
    """网易yeah.net邮箱提供者。

    继承自网易163邮箱提供者，仅修改服务器地址。
    """

    @property
    def name(self) -> str:
        """服务商名称。

        Returns:
            网易yeah邮箱的可读名称。
        """
        return "网易able邮箱"

    @property
    def default_config(self) -> ProviderConfig:
        """网易able邮箱默认配置。

        Returns:
            网易able邮箱的IMAP/SMTP服务器配置。
        """
        return ProviderConfig(
            imap_host="imap.yeah.net",
            imap_port=993,
            smtp_host="smtp.yeah.net",
            smtp_port=465,
            use_ssl=True,
        )
