"""日志格式化器。"""

from __future__ import annotations

import logging


class StandardFileFormatter(logging.Formatter):
    """文件日志格式化器。"""

    def __init__(self) -> None:
        """初始化格式化器。"""
        super().__init__(
            fmt=(
                "%(asctime)s | %(levelname)s | %(name)s | "
                "%(filename)s:%(lineno)d | %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
