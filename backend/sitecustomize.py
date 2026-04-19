"""uvicorn 启动参数注入模块。"""

from __future__ import annotations

import os
import sys


class UvicornEnvInjector:
    """uvicorn 启动参数注入器。

    该注入器用于在启动 uvicorn CLI 时自动补齐 host/port/reload/log_level 参数。
    """

    def apply(self) -> None:
        """根据环境变量注入启动参数。"""
        if not self._is_uvicorn_command():
            return

        host = self._get_str("HOST", "0.0.0.0")
        port = self._get_int("PORT", 10003)
        reload_enabled = self._get_bool("RELOAD", False)
        log_level = self._get_str("LOG_LEVEL", "INFO").lower()

        if not self._has_option("--host"):
            sys.argv.extend(["--host", host])

        if not self._has_option("--port"):
            sys.argv.extend(["--port", str(port)])

        if reload_enabled and not self._has_option("--reload"):
            sys.argv.append("--reload")

        if log_level and not self._has_option("--log-level"):
            sys.argv.extend(["--log-level", log_level])

    def _is_uvicorn_command(self) -> bool:
        """判断当前命令是否为 uvicorn。

        Returns:
            是否为 uvicorn 命令。
        """
        executable = os.path.basename(sys.argv[0]).lower()
        return executable in {"uvicorn", "uvicorn.exe"}

    def _has_option(self, option: str) -> bool:
        """判断是否已传入指定参数。

        Args:
            option: 参数名称。

        Returns:
            是否已传入。
        """
        prefix = f"{option}="
        return option in sys.argv or any(arg.startswith(prefix) for arg in sys.argv)

    def _get_str(self, key: str, default: str) -> str:
        """读取字符串参数。

        Args:
            key: 环境变量名。
            default: 默认值。

        Returns:
            字符串结果。
        """
        value = os.getenv(key)
        if value is None or value.strip() == "":
            return default
        return value

    def _get_int(self, key: str, default: int) -> int:
        """读取整数参数。

        Args:
            key: 环境变量名。
            default: 默认值。

        Returns:
            整数结果。
        """
        value = os.getenv(key)
        if value is None or value.strip() == "":
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _get_bool(self, key: str, default: bool) -> bool:
        """读取布尔参数。

        Args:
            key: 环境变量名。
            default: 默认值。

        Returns:
            布尔结果。
        """
        value = os.getenv(key)
        if value is None or value.strip() == "":
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}


UvicornEnvInjector().apply()
