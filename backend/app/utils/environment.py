"""环境变量读取工具。"""

from __future__ import annotations

import os
from pathlib import Path


class EnvReader:
    """环境变量读取器。"""

    _env_cache: dict = {}

    @classmethod
    def _load_env_file(cls) -> None:
        """加载.env文件。"""
        if cls._env_cache:
            return
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            cls._env_cache[key.strip()] = value.strip()
        for key, value in cls._env_cache.items():
            if key not in os.environ:
                os.environ[key] = value

    def get_str(self, key: str, default: str | None = None) -> str | None:
        """读取字符串配置。"""
        self._load_env_file()
        value = os.getenv(key)
        if value is None or value.strip() == "":
            return default
        return value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """读取布尔配置。"""
        self._load_env_file()
        value = self.get_str(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def get_int(self, key: str, default: int) -> int:
        """读取整数配置。"""
        self._load_env_file()
        value = self.get_str(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default