"""IMAP响应解析工具模块。"""

from __future__ import annotations

import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Iterable, List, Optional, Tuple


class ImapResponseParser:
    """IMAP响应解析器。

    负责从FETCH响应中提取正文、标志位与内部日期。
    """

    @staticmethod
    def extract_literal_bytes(lines: Iterable[object]) -> Optional[bytes]:
        """提取FETCH响应中的literal邮件内容。

        Args:
            lines: IMAP响应行列表。

        Returns:
            原始邮件字节或None。
        """
        size = ImapResponseParser._find_literal_size(lines)

        stream_result = ImapResponseParser._extract_literal_stream(lines, size)
        if stream_result:
            return stream_result

        return ImapResponseParser._extract_literal_from_buffer(lines, size)

    @staticmethod
    def parse_flags_and_internal_date(
        lines: Iterable[object],
    ) -> Tuple[List[str], Optional[datetime], Optional[int]]:
        """解析FETCH响应中的flags与internal date。

        Args:
            lines: IMAP响应行列表。

        Returns:
            (flags列表, internal_date, size)。
        """
        header_line = ImapResponseParser._find_header_line(lines)
        if not header_line:
            return [], None, None

        flags_match = re.search(r"FLAGS \((.*?)\)", header_line)
        flags = flags_match.group(1).split() if flags_match else []

        date_match = re.search(r'INTERNALDATE "([^"]+)"', header_line)
        internal_date = (
            ImapResponseParser._parse_internal_date(date_match.group(1))
            if date_match
            else None
        )

        size_match = re.search(r"RFC822\.SIZE (\d+)", header_line)
        size = int(size_match.group(1)) if size_match else None

        return flags, internal_date, size

    @staticmethod
    def _extract_literal_stream(
        lines: Iterable[object],
        literal_size: Optional[int],
    ) -> Optional[bytes]:
        """按IMAP流式响应解析literal内容。"""
        buffer = bytearray()
        remaining = 0
        collecting = False

        for line in lines:
            if not isinstance(line, (bytes, bytearray, memoryview)):
                continue
            data = bytes(line)

            if not collecting:
                if literal_size is None:
                    match = re.search(rb"\{(\d+)\}\r?\n?", data)
                    if not match:
                        continue
                    literal_size = int(match.group(1))
                else:
                    # 构建包含literal_size的正则表达式
                    pattern = rb"\{" + str(literal_size).encode() + rb"\}\r?\n?"
                    match = re.search(pattern, data)
                    if not match:
                        continue
                start = match.end()
                literal_part = data[start:]
                if literal_size is None:
                    return None
                if len(literal_part) >= literal_size:
                    return literal_part[:literal_size]

                buffer.extend(literal_part)
                remaining = literal_size - len(literal_part)
                collecting = True
                continue

            if len(data) >= remaining:
                buffer.extend(data[:remaining])
                return bytes(buffer)

            buffer.extend(data)
            remaining -= len(data)

        return None

    @staticmethod
    def _extract_literal_from_buffer(
        lines: Iterable[object],
        literal_size: Optional[int],
    ) -> Optional[bytes]:
        """从拼接后的响应中回退解析literal内容。"""
        all_bytes = ImapResponseParser._collect_bytes(lines)
        if not all_bytes:
            return None

        if literal_size is None:
            match = re.search(rb"\{(\d+)\}", all_bytes)
            if not match:
                return None
            literal_size = int(match.group(1))
            marker = match.group(0)
        else:
            marker = f"{{{literal_size}}}".encode()

        marker_index = all_bytes.rfind(marker)
        if marker_index == -1:
            return None

        start = marker_index + len(marker)
        if all_bytes[start : start + 2] == b"\r\n":
            start += 2
        elif all_bytes[start : start + 1] == b"\n":
            start += 1

        end = start + literal_size
        if end > len(all_bytes):
            return None

        return all_bytes[start:end]

    @staticmethod
    def _find_literal_size(lines: Iterable[object]) -> Optional[int]:
        """从FETCH响应头中解析literal大小。"""
        header_line = ImapResponseParser._find_header_line(lines)
        if header_line:
            match = re.search(r"\{(\d+)\}", header_line)
            if match:
                return int(match.group(1))

        all_bytes = ImapResponseParser._collect_bytes(lines)
        if not all_bytes:
            return None

        match = re.search(rb"\{(\d+)\}", all_bytes)
        if match:
            return int(match.group(1))

        return None

    @staticmethod
    def _collect_bytes(lines: Iterable[object]) -> bytes:
        """合并响应中的字节内容。

        Args:
            lines: 响应行列表。

        Returns:
            合并后的字节内容。
        """
        chunks = []
        for line in lines:
            if isinstance(line, (bytes, bytearray, memoryview)):
                chunks.append(bytes(line))
        return b"".join(chunks)

    @staticmethod
    def _find_header_line(lines: Iterable[object]) -> Optional[str]:
        """查找包含FETCH元数据的响应头。

        Args:
            lines: 响应行列表。

        Returns:
            解析到的头部文本。
        """
        for line in lines:
            if not isinstance(line, (bytes, bytearray)):
                continue
            text = line.decode("utf-8", errors="ignore")
            if "FETCH" in text:
                return text
        return None

    @staticmethod
    def _parse_internal_date(date_str: str) -> Optional[datetime]:
        """解析IMAP内部日期。

        Args:
            date_str: 日期字符串。

        Returns:
            日期对象或None。
        """
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            try:
                return datetime.strptime(date_str, "%d-%b-%Y %H:%M:%S %z")
            except Exception:
                return None
