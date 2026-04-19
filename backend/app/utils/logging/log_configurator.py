"""日志配置器。"""

from __future__ import annotations

import logging
import os
import sys
import warnings

from uvicorn.logging import DefaultFormatter

from app.core.config import AppConfig
from app.utils.logging.line_count_rotating_handler import LineCountRotatingFileHandler
from app.utils.logging.log_formatter import StandardFileFormatter


class LogConfigurator:
    """日志配置器。"""

    def __init__(self, config: AppConfig) -> None:
        """初始化配置器。

        Args:
            config: 应用配置。
        """
        self._config = config

    def configure(self) -> None:
        """应用日志配置。"""
        # 首先禁用absl和tensorflow的日志
        self._suppress_noisy_libraries()

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(self._config.log_level)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            DefaultFormatter(
                fmt="%(levelprefix)s %(asctime)s | %(filename)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        file_handler = LineCountRotatingFileHandler(
            self._config.log_dir, self._config.log_max_lines
        )
        file_handler.setFormatter(StandardFileFormatter())

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        self._configure_child_loggers()

    def _suppress_noisy_libraries(self) -> None:
        """抑制嘈杂的第三方库日志输出。"""
        # 设置环境变量抑制TensorFlow日志
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # 只显示ERROR
        os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
        os.environ["GRPC_VERBOSITY"] = "ERROR"
        os.environ["GLOG_minloglevel"] = "2"

        # 抑制Python警告
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

    def _configure_child_loggers(self) -> None:
        """统一配置第三方日志。"""
        # Uvicorn相关
        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(self._config.log_level)
            logger.propagate = True

        # TensorFlow和Keras相关 - 设置为WARNING级别以抑制大量DEBUG日志
        noisy_loggers = [
            "tensorflow",
            "tf",
            "keras",
            "absl",
            "h5py",
            "matplotlib",
            "PIL",
            "numba",
            "onnx",
            "onnxruntime",
            "google",
            "urllib3",
            "filelock",
            "asyncio",
        ]
        for logger_name in noisy_loggers:
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.WARNING)
            logger.propagate = True

        # SQLAlchemy - 保持INFO级别但使用统一格式
        for logger_name in ("sqlalchemy", "sqlalchemy.engine", "sqlalchemy.pool"):
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.WARNING)
            logger.propagate = True
