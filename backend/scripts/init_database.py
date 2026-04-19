"""
数据库初始化脚本。

用于创建 argus_mail 数据库和所有数据表。
"""

import asyncio
import sys
from pathlib import Path

# 将backend目录添加到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import aiomysql

from app.core.config import AppConfigLoader
from app.core.database import DatabaseManager


class DatabaseInitializer:
    """数据库初始化器。

    负责创建数据库和所有数据表。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "123456",
        database: str = "Argus",
    ) -> None:
        """初始化数据库初始化器。

        Args:
            host: 数据库主机地址。
            port: 数据库端口。
            user: 数据库用户名。
            password: 数据库密码。
            database: 数据库名称。
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database

    async def create_database(self) -> None:
        """创建数据库（如果不存在）。"""
        connection = await aiomysql.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
        )

        try:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {self._database} "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                print(f"✓ 数据库 {self._database} 创建成功（或已存在）")
        finally:
            connection.close()

    async def create_tables(self) -> None:
        """创建所有数据表。"""
        # 导入所有实体以确保它们被注册到Base.metadata
        from app.entities.user_entity import UserEntity  # noqa: F401
        from app.entities.email_account_entity import EmailAccountEntity  # noqa: F401
        from app.entities.email_entity import EmailEntity  # noqa: F401
        from app.entities.system_settings_entity import SystemSettingsEntity  # noqa: F401

        db_url = (
            f"mysql+aiomysql://{self._user}:{self._password}"
            f"@{self._host}:{self._port}/{self._database}?charset=utf8mb4"
        )

        db_manager = DatabaseManager(db_url)
        await db_manager.create_tables()
        await db_manager.close()
        print("✓ 所有数据表创建成功")

    async def run(self) -> None:
        """执行完整的初始化流程。"""
        print("开始初始化数据库...")
        await self.create_database()
        await self.create_tables()
        print("数据库初始化完成！")


async def main():
    """主入口函数。"""
    initializer = DatabaseInitializer()
    await initializer.run()


if __name__ == "__main__":
    asyncio.run(main())