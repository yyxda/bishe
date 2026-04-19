"""CRUD 日志工具。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict


class CrudLogEntry:
    """CRUD 日志条目构建器。"""

    def __init__(
        self,
        action: str,
        resource: str,
        detail: str = "",
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """初始化日志条目。

        Args:
            action: CRUD 动作。
            resource: 资源名称。
            detail: 业务描述。
            metadata: 结构化附加信息。
        """
        self._action = action
        self._resource = resource
        self._detail = detail
        self._metadata = metadata or {}

    def to_message(self) -> str:
        """生成日志文本。

        Returns:
            日志文本。
        """
        parts = [f"action={self._action}", f"resource={self._resource}"]
        if self._detail:
            parts.append(f"detail={self._detail}")
        if self._metadata:
            parts.append(
                f"meta={json.dumps(self._metadata, ensure_ascii=False, separators=(',', ':'))}"
            )
        return " | ".join(parts)


class CrudLogger:
    """CRUD 日志记录器。"""

    def __init__(self, logger: logging.Logger, resource: str) -> None:
        """初始化 CRUD 日志记录器。

        Args:
            logger: Python 日志对象。
            resource: 资源名称。
        """
        self._logger = logger
        self._resource = resource

    def log_create(self, detail: str, metadata: Dict[str, Any] | None = None) -> None:
        """记录新增操作。

        Args:
            detail: 业务描述。
            metadata: 附加信息。
        """
        self._log("CREATE", detail, metadata)

    def log_read(self, detail: str, metadata: Dict[str, Any] | None = None) -> None:
        """记录查询操作。

        Args:
            detail: 业务描述。
            metadata: 附加信息。
        """
        self._log("READ", detail, metadata)

    def log_update(self, detail: str, metadata: Dict[str, Any] | None = None) -> None:
        """记录更新操作。

        Args:
            detail: 业务描述。
            metadata: 附加信息。
        """
        self._log("UPDATE", detail, metadata)

    def log_delete(self, detail: str, metadata: Dict[str, Any] | None = None) -> None:
        """记录删除操作。

        Args:
            detail: 业务描述。
            metadata: 附加信息。
        """
        self._log("DELETE", detail, metadata)

    def _log(self, action: str, detail: str, metadata: Dict[str, Any] | None) -> None:
        """写入 CRUD 日志。

        Args:
            action: 动作名称。
            detail: 业务描述。
            metadata: 附加信息。
        """
        entry = CrudLogEntry(action, self._resource, detail, metadata)
        self._logger.info(entry.to_message())
