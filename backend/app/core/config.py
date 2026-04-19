"""应用配置模块。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from app.utils.environment import EnvReader


def _default_log_dir() -> Path:
    """获取默认日志目录。

    Returns:
        默认日志目录路径。
    """
    return Path(__file__).resolve().parents[3] / "logs"

DEFAULT_CORS_ORIGINS = [
    "http://localhost:10002",
    "http://127.0.0.1:10002",
    "http://0.0.0.0:10002",
]


def _parse_cors_origins(raw_value: str | None, fallback: List[str]) -> List[str]:
    """解析跨域白名单配置。

    Args:
        raw_value: 环境变量中的CORS原始字符串。
        fallback: 默认白名单列表。

    Returns:
        解析后的跨域白名单列表。
    """
    if not raw_value:
        return list(fallback)

    normalized = raw_value.replace(";", ",")
    origins = [origin.strip() for origin in normalized.split(",") if origin.strip()]
    return origins or list(fallback)


@dataclass(frozen=True)
class AppConfig:
    """应用运行配置。

    Attributes:
        app_name: 应用名称。
        api_prefix: API 路由前缀。
        cors_origins: 允许的跨域来源列表。
        cors_allow_all: 是否允许所有跨域来源。
        host: 服务监听地址。
        port: 服务监听端口。
        reload: 是否自动重载。
        log_level: 日志等级。
        log_dir: 日志目录。
        log_max_lines: 单个日志文件最大行数。
        db_host: 数据库主机地址。
        db_port: 数据库端口。
        db_user: 数据库用户名。
        db_password: 数据库密码。
        db_name: 数据库名称。
        db_pool_size: 连接池大小。
        db_max_overflow: 连接池最大溢出连接数。
        db_pool_recycle: 连接回收时间（秒）。
        api_key: API 密钥，仅从环境读取。
    """

    app_name: str = "Argus 校园网钓鱼邮件智能过滤系统"
    api_prefix: str = "/api"
    cors_origins: List[str] = field(
        default_factory=lambda: list(DEFAULT_CORS_ORIGINS)
    )
    cors_allow_all: bool = False
    host: str = "0.0.0.0"
    port: int = 10003
    reload: bool = True
    log_level: str = "INFO"
    log_dir: Path = field(default_factory=_default_log_dir)
    log_max_lines: int = 1000
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "argus_mail"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    api_key: str | None = None
    bert_model_path: str | None = None
    enable_rule_based_detection: bool = False

    def get_database_url(self) -> str:
        """生成数据库连接URL。

        Returns:
            符合SQLAlchemy格式的异步MySQL连接URL。
        """
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


class AppConfigLoader:
    """应用配置加载器。"""

    def __init__(self, env_path: Path | None = None) -> None:
        """初始化配置加载器。

        Args:
            env_path: .env 文件路径。
        """
        self._env_path = env_path or self._default_env_path()
        self._env_reader = EnvReader()

    def load(self) -> AppConfig:
        """加载配置。

        Returns:
            应用配置。
        """
        log_dir = self._resolve_log_dir()

        return AppConfig(
            host=self._env_reader.get_str("HOST", "0.0.0.0"),
            port=self._env_reader.get_int("PORT", 10003),
            reload=self._env_reader.get_bool("RELOAD", True),
            log_level=self._env_reader.get_str("LOG_LEVEL", "INFO"),
            log_dir=log_dir,
            log_max_lines=self._env_reader.get_int("LOG_MAX_LINES", 1000),
            cors_origins=_parse_cors_origins(
                self._env_reader.get_str("CORS_ORIGINS"),
                DEFAULT_CORS_ORIGINS,
            ),
            cors_allow_all=self._env_reader.get_bool("CORS_ALLOW_ALL", False),
            db_host=self._env_reader.get_str("DB_HOST", "127.0.0.1"),
            db_port=self._env_reader.get_int("DB_PORT", 3306),
            db_user=self._env_reader.get_str("DB_USER", "root"),
            db_password=self._env_reader.get_str("DB_PASSWORD", ""),
            db_name=self._env_reader.get_str("DB_NAME", "argus_mail"),
            db_pool_size=self._env_reader.get_int("DB_POOL_SIZE", 10),
            db_max_overflow=self._env_reader.get_int("DB_MAX_OVERFLOW", 20),
            db_pool_recycle=self._env_reader.get_int("DB_POOL_RECYCLE", 3600),
            api_key=self._env_reader.get_str("API_KEY"),
            bert_model_path=self._env_reader.get_str("BERT_MODEL_PATH"),
            enable_rule_based_detection=self._env_reader.get_bool("ENABLE_RULE_BASED_DETECTION", False),
        )

    def _resolve_log_dir(self) -> Path:
        """解析日志目录。

        Returns:
            日志目录路径。
        """
        env_value = self._env_reader.get_str("LOG_DIR")
        if env_value:
            return Path(env_value)

        backend_root = self._env_path.parent
        return backend_root.parent / "logs"

    def _default_env_path(self) -> Path:
        """获取默认 .env 路径。

        Returns:
            .env 文件路径。
        """
        return Path(__file__).resolve().parents[2] / ".env"