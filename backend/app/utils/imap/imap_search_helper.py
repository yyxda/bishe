"""IMAP搜索辅助工具模块。

封装与搜索命令相关的公共逻辑，避免IMAP客户端文件过长。
"""

from __future__ import annotations

from logging import Logger
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from aioimaplib import IMAP4_SSL


class ImapSearchHelper:
    """IMAP搜索辅助工具类。"""

    @staticmethod
    def extract_search_numbers(lines: list) -> List[int]:
        """从SEARCH响应中提取数字列表。

        Args:
            lines: 搜索响应行列表。

        Returns:
            提取到的数字列表。
        """
        numbers: List[int] = []
        for line in lines:
            if isinstance(line, (bytes, bytearray)):
                line = line.decode("utf-8", errors="ignore")
            for value in str(line).split():
                if value.isdigit():
                    numbers.append(int(value))
        return numbers

    @staticmethod
    async def uid_search_raw(
        client: "IMAP4_SSL",
        start_uid: int,
        logger: Optional[Logger] = None,
    ):
        """使用原始协议发送UID SEARCH命令。

        Args:
            client: IMAP客户端实例。
            start_uid: 起始UID（包含）。
            logger: 可选日志记录器。

        Returns:
            aioimaplib命令响应或None。
        """
        if not client:
            if logger:
                logger.error("IMAP未连接")
            return None

        try:
            # 使用协议层的search接口，避免CHARSET并保留SEARCH的未标记响应。
            return await client.protocol.search(
                f"{start_uid}:*",
                charset=None,
                by_uid=True,
            )
        except Exception as exc:
            if logger:
                logger.warning("UID SEARCH原始命令执行失败: %s", exc)
            return None
