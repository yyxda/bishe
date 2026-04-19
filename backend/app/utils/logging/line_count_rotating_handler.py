"""按行数轮转的日志处理器。"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Tuple


class LineCountRotatingFileHandler(logging.Handler):
    """按行数轮转的文件日志处理器。"""

    def __init__(
        self,
        log_dir: Path,
        max_lines: int,
        encoding: str = "utf-8",
    ) -> None:
        """初始化处理器。

        Args:
            log_dir: 日志目录。
            max_lines: 单个日志文件最大行数。
            encoding: 文件编码。
        """
        super().__init__()
        self._log_dir = log_dir
        self._max_lines = max_lines
        self._encoding = encoding
        self._current_date = ""
        self._sequence = 0
        self._line_count = 0
        self._stream = None
        self._initialize_stream()

    def emit(self, record: logging.LogRecord) -> None:
        """输出日志记录。

        Args:
            record: 日志记录。
        """
        try:
            self._ensure_stream()
            message = self.format(record)
            line_count = self._count_lines(message)

            if self._line_count + line_count > self._max_lines:
                self._rotate_file()

            self._write_message(message)
            self._line_count += line_count
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """关闭日志流。"""
        if self._stream:
            self._stream.close()
            self._stream = None
        super().close()

    def _initialize_stream(self) -> None:
        """初始化日志文件。"""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._current_date = datetime.date.today().isoformat()
        self._sequence, self._line_count = self._resolve_state(self._current_date)
        self._open_stream()

    def _ensure_stream(self) -> None:
        """确保日志流可用。"""
        today = datetime.date.today().isoformat()
        if today != self._current_date:
            self._current_date = today
            self._sequence, self._line_count = self._resolve_state(today)
            self._open_stream()

    def _resolve_state(self, date_str: str) -> Tuple[int, int]:
        """解析当前日期的日志文件状态。

        Args:
            date_str: 当前日期字符串。

        Returns:
            序号与当前行数。
        """
        candidates = list(self._log_dir.glob(f"{date_str}-*.log"))
        if not candidates:
            return 1, 0

        last_file = max(candidates, key=lambda path: self._parse_sequence(path.name))
        sequence = self._parse_sequence(last_file.name)
        line_count = self._count_file_lines(last_file)

        if line_count >= self._max_lines:
            return sequence + 1, 0

        return max(sequence, 1), line_count

    def _open_stream(self) -> None:
        """打开日志文件流。"""
        if self._stream:
            self._stream.close()

        log_path = self._build_log_path(self._current_date, self._sequence)
        self._stream = log_path.open("a", encoding=self._encoding)

    def _rotate_file(self) -> None:
        """触发日志轮转。"""
        self._sequence += 1
        self._line_count = 0
        self._open_stream()

    def _build_log_path(self, date_str: str, sequence: int) -> Path:
        """构建日志文件路径。

        Args:
            date_str: 日期字符串。
            sequence: 序号。

        Returns:
            日志文件路径。
        """
        return self._log_dir / f"{date_str}-{sequence:02d}.log"

    def _parse_sequence(self, filename: str) -> int:
        """解析文件序号。

        Args:
            filename: 文件名。

        Returns:
            序号。
        """
        try:
            sequence_part = filename.split("-")[-1].split(".")[0]
            return int(sequence_part)
        except (ValueError, IndexError):
            return 0

    def _count_file_lines(self, path: Path) -> int:
        """统计日志文件行数。

        Args:
            path: 文件路径。

        Returns:
            行数。
        """
        try:
            with path.open("r", encoding=self._encoding) as file:
                return sum(1 for _ in file)
        except FileNotFoundError:
            return 0

    def _count_lines(self, message: str) -> int:
        """统计消息行数。

        Args:
            message: 日志消息。

        Returns:
            行数。
        """
        lines = message.splitlines()
        return max(len(lines), 1)

    def _write_message(self, message: str) -> None:
        """写入日志内容。

        Args:
            message: 日志消息。
        """
        if not self._stream:
            return

        self._stream.write(message + "\n")
        self._stream.flush()
