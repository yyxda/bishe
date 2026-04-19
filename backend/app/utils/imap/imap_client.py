"""异步IMAP客户端模块。

基于aioimaplib封装的异步IMAP邮件客户端，支持增量同步与文件夹遍历。
通过Provider架构支持不同邮箱服务商的特定处理逻辑。
"""

from __future__ import annotations

import logging
import re
import ssl
from typing import List, Optional, TYPE_CHECKING

from aioimaplib import IMAP4_SSL

from app.utils.imap.imap_models import FetchedEmail, MailboxInfo, MailboxStatus
from app.utils.imap.imap_response_parser import ImapResponseParser
from app.utils.imap.imap_search_helper import ImapSearchHelper

if TYPE_CHECKING:
    from app.utils.imap.providers.base_provider import BaseEmailProvider


class ImapClient:
    """异步IMAP客户端类。

    提供连接、文件夹列表、增量UID同步等能力。
    通过Provider模式支持不同邮箱服务商的特定处理。

    Attributes:
        provider: 邮箱服务商提供者，处理服务商特定的逻辑。

    Example:
        >>> from app.utils.imap.providers import ProviderFactory
        >>> from app.entities.email_account_entity import EmailType
        >>>
        >>> provider = ProviderFactory.get_provider(EmailType.NETEASE)
        >>> client = ImapClient(provider=provider)
        >>> await client.connect("user@163.com", "password")
    """

    def __init__(
        self,
        config=None,
        logger: Optional[logging.Logger] = None,
        provider: Optional["BaseEmailProvider"] = None,
    ):
        """初始化IMAP客户端。

        Args:
            config: IMAP配置（兼容旧接口）。如果提供provider，则优先使用provider的配置。
            logger: 日志记录器。
            provider: 邮箱服务商提供者。
        """
        self._provider = provider
        self._logger = logger or logging.getLogger(self.__class__.__name__)

        # 配置优先级：provider.default_config > config
        if provider:
            provider_config = provider.default_config
            self._imap_host = config.imap_host if config else provider_config.imap_host
            self._imap_port = config.imap_port if config else provider_config.imap_port
        elif config:
            self._imap_host = config.imap_host
            self._imap_port = config.imap_port
        else:
            raise ValueError("必须提供config或provider参数")

        self._client: Optional[IMAP4_SSL] = None
        self._selected_mailbox: Optional[str] = None

    @property
    def provider(self) -> Optional["BaseEmailProvider"]:
        """获取当前的服务商提供者。

        Returns:
            服务商提供者实例，如果未设置则返回None。
        """
        return self._provider

    async def connect(self, username: str, password: str) -> bool:
        """连接并登录IMAP服务器。

        Args:
            username: 用户名（通常是邮箱地址）。
            password: 授权密码。

        Returns:
            是否连接成功。
        """
        try:
            # 获取超时时间（Provider可自定义，默认60秒）
            timeout = 60
            if self._provider:
                timeout = self._provider.get_connection_timeout()
            
            # 确保最小超时时间为60秒
            timeout = max(timeout, 60)

            # 创建SSL上下文，确保连接能正常建立
            ssl_context = ssl.create_default_context()

            self._client = IMAP4_SSL(
                host=self._imap_host,
                port=self._imap_port,
                timeout=timeout,
                ssl_context=ssl_context,
            )
            await self._client.wait_hello_from_server()

            response = await self._client.login(username, password)
            if response.result != "OK":
                self._logger.warning("IMAP登录失败: %s", response)
                return False

            # 调用Provider的登录后钩子（如发送ID命令）
            await self._execute_post_login_hook()

            self._logger.info("IMAP连接成功: %s", username)
            return True
        except Exception as exc:
            self._logger.error("IMAP连接异常: %s (type: %s)", exc, type(exc).__name__)
            return False

    async def disconnect(self) -> None:
        """断开IMAP连接。"""
        if self._client:
            try:
                await self._client.logout()
            except Exception as exc:
                self._logger.warning("IMAP断开连接异常: %s", exc)
            finally:
                self._client = None
                self._selected_mailbox = None

    async def list_mailboxes(self) -> List[MailboxInfo]:
        """获取邮箱文件夹列表。

        Returns:
            文件夹信息列表。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return []

        response = await self._safe_list()
        if response.result != "OK":
            self._logger.warning("获取文件夹列表失败: %s", response)
            return []

        mailboxes = []
        for line in response.lines:
            if not isinstance(line, (bytes, bytearray)):
                continue
            info = self._parse_list_line(line.decode("utf-8", errors="ignore"))
            if info:
                mailboxes.append(info)

        return mailboxes

    async def get_mailbox_status(self, mailbox_name: str) -> MailboxStatus:
        """获取文件夹状态信息。

        Args:
            mailbox_name: 文件夹名称。

        Returns:
            文件夹状态。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return MailboxStatus(None, None, None)

        response = await self._client.status(
            self._format_mailbox_name(mailbox_name),
            "(UIDVALIDITY UIDNEXT MESSAGES UNSEEN)",
        )
        if response.result != "OK":
            self._logger.warning("获取文件夹状态失败: %s", response)
            return MailboxStatus(None, None, None)

        line = ""
        for resp_line in response.lines:
            if isinstance(resp_line, (bytes, bytearray)):
                line = resp_line.decode("utf-8", errors="ignore")
                break

        uid_validity = self._parse_status_value(line, "UIDVALIDITY")
        uid_next = self._parse_status_value(line, "UIDNEXT")
        message_count = self._parse_status_value(line, "MESSAGES")

        return MailboxStatus(
            uid_validity=uid_validity,
            uid_next=uid_next,
            message_count=message_count,
        )

    async def select_mailbox(self, mailbox_name: str) -> bool:
        """选择文件夹用于后续操作。

        Args:
            mailbox_name: 文件夹名称。

        Returns:
            是否选择成功。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return False

        # 调用Provider的选择前钩子
        if self._provider:
            if not await self._provider.pre_select_hook(self._client, mailbox_name):
                self._logger.warning("Provider拒绝选择文件夹: %s", mailbox_name)
                return False

        response = await self._client.select(self._format_mailbox_name(mailbox_name))
        if response.result != "OK":
            self._logger.warning("选择文件夹失败: %s", response)
            return False

        self._selected_mailbox = mailbox_name

        # 调用Provider的选择后钩子
        if self._provider:
            await self._provider.post_select_hook(self._client, mailbox_name)

        return True

    async def fetch_uids_since(self, start_uid: int) -> List[int]:
        """获取指定UID之后的UID列表。

        Args:
            start_uid: 起始UID（包含）。

        Returns:
            UID列表。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return []

        start_uid = max(start_uid, 1)
        self._logger.info("[fetch_uids_since] 开始获取UID，start_uid=%d", start_uid)
        
        # 方法1：直接使用FETCH命令获取所有UID（最可靠的方式）
        try:
            # 使用 1:* 获取所有邮件的UID
            response = await self._client.fetch("1:*", "(UID)")
            
            if response.result == "OK":
                self._logger.info("[fetch_uids_since] FETCH 1:* 命令执行成功")
                real_uids = []
                for line in response.lines:
                    if isinstance(line, (bytes, bytearray)):
                        line = line.decode("utf-8", errors="ignore")
                    # 解析UID
                    import re
                    match = re.search(r"UID (\d+)", line)
                    if match:
                        uid = int(match.group(1))
                        if uid >= start_uid:
                            real_uids.append(uid)
                
                self._logger.info("[fetch_uids_since] 成功获取 %d 个UID", len(real_uids))
                return sorted(real_uids)
            else:
                self._logger.warning("[fetch_uids_since] FETCH 1:* 命令执行失败: %s", response)
        except Exception as e:
            self._logger.error("[fetch_uids_since] FETCH 1:* 命令执行异常: %s", str(e))
        
        # 方法2：使用SEARCH命令获取所有邮件的序列号，然后批量获取UID
        try:
            # 使用SEARCH命令获取所有邮件的序列号
            response = await self._client.search("ALL")
            
            if response.result == "OK":
                self._logger.info("[fetch_uids_since] SEARCH命令执行成功")
                # 提取序列号
                seq_nums = ImapSearchHelper.extract_search_numbers(response.lines)
                self._logger.info("[fetch_uids_since] 找到 %d 个序列号", len(seq_nums))
                
                if not seq_nums:
                    return []
                
                # 批量获取UID
                real_uids = []
                batch_size = 100
                for i in range(0, len(seq_nums), batch_size):
                    batch = seq_nums[i:i + batch_size]
                    seq_set = ",".join(map(str, batch))
                    
                    fetched_response = await self._client.fetch(seq_set, "(UID)")
                    if fetched_response.result == "OK":
                        for line in fetched_response.lines:
                            if isinstance(line, (bytes, bytearray)):
                                line = line.decode("utf-8", errors="ignore")
                            # 解析UID
                            import re
                            match = re.search(r"UID (\d+)", line)
                            if match:
                                uid = int(match.group(1))
                                if uid >= start_uid:
                                    real_uids.append(uid)
                
                self._logger.info("[fetch_uids_since] 成功获取 %d 个UID", len(real_uids))
                return sorted(real_uids)
            else:
                self._logger.warning("[fetch_uids_since] SEARCH命令执行失败: %s", response)
        except Exception as e:
            self._logger.error("[fetch_uids_since] SEARCH命令执行异常: %s", str(e))
        
        # 尝试使用STATUS命令获取邮件总数，然后获取所有邮件
        try:
            # 获取邮箱状态，获取邮件总数
            status_response = await self._client.status("INBOX", "(MESSAGES)")
            if status_response.result == "OK":
                # 解析邮件总数
                import re
                for line in status_response.lines:
                    if isinstance(line, (bytes, bytearray)):
                        line = line.decode("utf-8", errors="ignore")
                    match = re.search(r"MESSAGES (\d+)", line)
                    if match:
                        message_count = int(match.group(1))
                        self._logger.info("[fetch_uids_since] 邮箱中有 %d 封邮件", message_count)
                        
                        # 获取所有邮件的UID
                        if message_count > 0:
                            fetch_response = await self._client.fetch(f"1:{message_count}", "(UID)")
                            if fetch_response.result == "OK":
                                real_uids = []
                                for line in fetch_response.lines:
                                    if isinstance(line, (bytes, bytearray)):
                                        line = line.decode("utf-8", errors="ignore")
                                    match = re.search(r"UID (\d+)", line)
                                    if match:
                                        uid = int(match.group(1))
                                        if uid >= start_uid:
                                            real_uids.append(uid)
                                
                                self._logger.info("[fetch_uids_since] 成功获取 %d 个UID", len(real_uids))
                                return sorted(real_uids)
        except Exception as e:
            self._logger.error("[fetch_uids_since] 获取邮件总数异常: %s", str(e))
        
        # 尝试使用最简单的方式：直接获取所有邮件
        try:
            # 直接获取所有邮件的UID
            response = await self._client.fetch("1:*", "(UID)")
            if response.result == "OK":
                self._logger.info("[fetch_uids_since] 直接FETCH命令执行成功")
                real_uids = []
                for line in response.lines:
                    if isinstance(line, (bytes, bytearray)):
                        line = line.decode("utf-8", errors="ignore")
                    match = re.search(r"UID (\d+)", line)
                    if match:
                        uid = int(match.group(1))
                        if uid >= start_uid:
                            real_uids.append(uid)
                
                self._logger.info("[fetch_uids_since] 成功获取 %d 个UID", len(real_uids))
                return sorted(real_uids)
        except Exception as e:
            self._logger.error("[fetch_uids_since] 直接FETCH命令执行异常: %s", str(e))
        
        return []

    async def fetch_latest_uids(self, count: int) -> List[int]:
        """获取最新的N封邮件的UID列表。

        使用IMAP序列号反向查找，避免获取全部UID列表。

        Args:
            count: 要获取的邮件数量。

        Returns:
            最新的N封邮件的UID列表（按UID升序排列）。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return []

        if count <= 0:
            return []

        # 使用 SEARCH ALL 获取邮件总数
        response = await self._client.search("ALL")
        if response.result != "OK":
            self._logger.warning("SEARCH ALL失败: %s", response)
            return []

        # 提取所有序列号
        seq_nums = ImapSearchHelper.extract_search_numbers(response.lines)
        if not seq_nums:
            return []

        # 取最后N个序列号（最新的邮件）
        seq_nums = sorted(seq_nums)
        latest_seq_nums = seq_nums[-count:] if len(seq_nums) > count else seq_nums

        # 批量获取这些序列号对应的UID
        seq_set = ",".join(map(str, latest_seq_nums))
        fetched_response = await self._client.fetch(seq_set, "(UID)")
        if fetched_response.result != "OK":
            self._logger.warning("获取UID详情失败: %s", fetched_response)
            return []

        real_uids = []
        for line in fetched_response.lines:
            if isinstance(line, (bytes, bytearray)):
                line = line.decode("utf-8", errors="ignore")

            match = re.search(r"UID (\d+)", line)
            if match:
                real_uids.append(int(match.group(1)))

        return sorted(real_uids)

    async def fetch_emails_by_uid(self, uids: List[int]) -> List[FetchedEmail]:
        """按UID列表抓取邮件原始内容。

        Args:
            uids: UID列表。

        Returns:
            抓取到的邮件列表。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return []

        self._logger.info("[fetch_emails_by_uid] 开始获取 %d 封邮件", len(uids))
        emails: List[FetchedEmail] = []
        success_count = 0
        failure_count = 0
        
        for i, uid in enumerate(uids, 1):
            try:
                self._logger.debug("[fetch_emails_by_uid] 正在获取邮件 %d/%d (UID=%d)", i, len(uids), uid)
                fetched = await self._fetch_email(uid)
                if fetched:
                    emails.append(fetched)
                    success_count += 1
                else:
                    failure_count += 1
                    self._logger.warning("[fetch_emails_by_uid] 邮件获取失败: UID=%d", uid)
            except Exception as e:
                failure_count += 1
                self._logger.error("[fetch_emails_by_uid] 获取邮件异常: UID=%d, 错误=%s", uid, str(e))
        
        self._logger.info("[fetch_emails_by_uid] 完成: 成功=%d, 失败=%d, 总计=%d", 
                        success_count, failure_count, len(uids))
        return emails

    async def _fetch_email(self, uid: int) -> Optional[FetchedEmail]:
        """抓取单封邮件内容。

        Args:
            uid: 邮件UID。

        Returns:
            抓取到的邮件对象或None。
        """
        response = await self._uid_command(
            "FETCH",
            str(uid),
            "(UID FLAGS INTERNALDATE RFC822.SIZE BODY.PEEK[])",
        )
        if response.result != "OK":
            self._logger.warning("FETCH失败: uid=%s", uid)
            return None

        raw_email = ImapResponseParser.extract_literal_bytes(response.lines)
        if not raw_email:
            self._logger.warning("邮件内容为空: uid=%s", uid)
            return None

        flags, internal_date, size = ImapResponseParser.parse_flags_and_internal_date(
            response.lines
        )

        return FetchedEmail(
            uid=uid,
            flags=flags,
            internal_date=internal_date,
            size=size,
            raw_bytes=raw_email,
        )

    async def _execute_post_login_hook(self) -> None:
        """执行登录后钩子。

        如果设置了Provider，调用其post_login_hook方法。
        否则使用默认的ID命令发送逻辑（兼容旧代码）。
        """
        if self._provider:
            # 使用Provider的钩子
            success = await self._provider.post_login_hook(self._client)
            if not success:
                self._logger.warning(
                    "Provider登录后钩子执行失败: %s",
                    self._provider.name if self._provider else "Unknown",
                )
        else:
            # 兼容旧代码：默认发送ID命令
            await self._send_id_command_default()

    async def _send_id_command_default(self) -> None:
        """默认的ID命令发送逻辑（兼容旧代码）。

        用于未设置Provider时的回退行为。
        """
        try:
            response = await self._client.id()
            if response.result == "OK":
                self._logger.debug("ID命令发送成功")
            else:
                self._logger.debug("ID命令响应: %s", response)
        except Exception as exc:
            self._logger.debug("ID命令发送失败（可忽略）: %s", exc)

    async def _safe_list(self):
        """兼容不同IMAP实现的LIST调用。"""
        try:
            return await self._client.list()
        except Exception:
            return await self._client.list('""', "*")

    async def _uid_command(self, command: str, *args):
        """执行UID命令，兼容部分客户端无UID方法的情况。"""
        command_upper = command.upper()
        if command_upper == "SEARCH":
            # aioimaplib的uid方法不支持SEARCH，改用SEARCH UID语法
            # 过滤掉None参数
            filtered_args = [arg for arg in args if arg is not None]
            return await self._client.search(*filtered_args)

        if hasattr(self._client, "uid"):
            return await self._client.uid(command, *args)

        # 如果没有uid方法，我们不能直接使用fetch，因为fetch使用的是序列号而不是UID
        raise ValueError(f"不支持的UID命令: {command} (客户端不支持UID命令)")

    def _parse_list_line(self, line: str) -> Optional[MailboxInfo]:
        """解析LIST响应行。

        Args:
            line: LIST响应行文本。

        Returns:
            文件夹信息或None。
        """
        if not line:
            return None

        match = re.match(r"\((?P<attrs>[^)]*)\)\s+(?P<rest>.*)", line)
        if not match:
            return None

        attrs = match.group("attrs").strip()
        rest = match.group("rest").strip()

        delimiter = None
        name = rest
        if rest.startswith('"'):
            parts = rest.split('"')
            if len(parts) >= 3:
                delimiter = parts[1]
                name = '"'.join(parts[2:]).strip()
        elif " " in rest:
            delimiter, name = rest.split(" ", 1)

        name = name.strip().strip('"')
        if not name:
            return None

        return MailboxInfo(name=name, delimiter=delimiter, attributes=attrs or None)

    def _parse_status_value(self, line: str, key: str) -> Optional[int]:
        """从STATUS响应中解析数值。

        Args:
            line: STATUS响应文本。
            key: 字段名称。

        Returns:
            数值或None。
        """
        if not line:
            return None
        match = re.search(rf"{key} (\d+)", line)
        return int(match.group(1)) if match else None

    def _format_mailbox_name(self, mailbox_name: str) -> str:
        """格式化文件夹名称。

        如果设置了Provider，使用Provider的格式化方法。
        否则使用默认的格式化逻辑。

        Args:
            mailbox_name: 原始文件夹名称。

        Returns:
            格式化后的文件夹名称。
        """
        if self._provider:
            return self._provider.format_mailbox_name(mailbox_name)

        # 默认格式化逻辑
        if not mailbox_name:
            return mailbox_name

        if mailbox_name.startswith('"') and mailbox_name.endswith('"'):
            return mailbox_name

        if " " in mailbox_name or '"' in mailbox_name:
            escaped = mailbox_name.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'

        return mailbox_name