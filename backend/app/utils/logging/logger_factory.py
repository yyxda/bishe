"""日志对象工厂。"""

from __future__ import annotations

import logging

from app.utils.logging.crud_logger import CrudLogger


class LoggerFactory:
    """日志工厂类。"""

    def create_logger(self, name: str) -> logging.Logger:
        """创建日志对象。

        Args:
            name: 日志名称。

        Returns:
            日志对象。
        """
        return logging.getLogger(name)

    def create_crud_logger(self, name: str, resource: str) -> CrudLogger:
        """创建 CRUD 日志记录器。

        Args:
            name: 日志名称。
            resource: 资源名称。

        Returns:
            CRUD 日志记录器。
        """
        return CrudLogger(self.create_logger(name), resource)
