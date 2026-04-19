"""
数据库连接管理模块。

提供异步数据库连接池和会话管理功能。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy ORM基类，所有实体模型继承此类。"""

    pass


class DatabaseManager:
    """
    数据库管理器类。

    负责管理数据库连接池、创建会话以及数据库的初始化和关闭。
    采用单例模式确保整个应用共享同一个数据库连接池。
    """

    def __init__(self, database_url: str) -> None:
        """
        初始化数据库管理器。

        Args:
            database_url: 数据库连接字符串，格式为
                mysql+aiomysql://user:password@host:port/database
        """
        self._database_url = database_url
        engine_kwargs = {
            "echo": False,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
        if self._database_url.startswith("sqlite"):
            # SQLite不支持连接池配置，使用NullPool避免多连接内存库失效。
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20

        self._engine = create_async_engine(self._database_url, **engine_kwargs)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话的上下文管理器。

        使用方式:
            async with db_manager.get_session() as session:
                # 执行数据库操作
                result = await session.execute(query)

        Yields:
            AsyncSession: 异步数据库会话对象

        Raises:
            Exception: 数据库操作异常时自动回滚事务
        """
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_tables(self) -> None:
        """
        创建所有数据库表。

        根据Base子类定义的模型自动创建对应的数据库表。
        仅在表不存在时创建，已存在的表不会被修改。
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """
        关闭数据库连接池。

        应在应用关闭时调用此方法释放数据库连接资源。
        """
        await self._engine.dispose()

    @property
    def engine(self):
        """获取数据库引擎实例。"""
        return self._engine


class DatabaseConfig:
    """
    数据库配置类。

    提供从环境变量或配置参数构建数据库连接URL的功能。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "argus_mail",
    ) -> None:
        """
        初始化数据库配置。

        Args:
            host: 数据库主机地址
            port: 数据库端口号
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def get_url(self) -> str:
        """
        生成数据库连接URL。

        Returns:
            str: 符合SQLAlchemy格式的异步MySQL连接URL
        """
        return (
            f"mysql+aiomysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}?charset=utf8mb4"
        )
