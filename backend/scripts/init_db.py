"""初始化数据库结构的脚本。"""

import asyncio
import sys
from pathlib import Path

# 确保以脚本方式执行时能正确导入backend下的app模块。
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.core.config import AppConfigLoader
from app.core.database import DatabaseManager
# 导入所有实体，确保SQLAlchemy注册表结构。
from app.entities import (  # noqa: F401
    user_entity,
    email_account_entity,
    email_entity,
    email_body_entity,
    email_recipient_entity,
    mailbox_entity,
    mailbox_message_entity,
    system_settings_entity,
)


async def main() -> None:
    """创建数据库表结构。"""
    config = AppConfigLoader().load()
    db_manager = DatabaseManager(config.get_database_url())
    try:
        await db_manager.create_tables()
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
