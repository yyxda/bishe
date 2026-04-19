"""添加规则检测开关字段到系统设置表"""

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.core.config import AppConfigLoader
from app.core.database import DatabaseManager
from sqlalchemy import text


async def migrate():
    """添加规则检测开关字段"""
    config = AppConfigLoader().load()
    db_manager = DatabaseManager(config.get_database_url())
    
    try:
        async with db_manager.get_session() as session:
            # 检查字段是否已存在
            check_sql = text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = :db_name
                AND TABLE_NAME = 'system_settings'
                AND COLUMN_NAME = 'enable_rule_based_detection'
            """)
            
            result = await session.execute(check_sql, {"db_name": config.db_name})
            count = result.scalar()
            
            if count > 0:
                print("字段 enable_rule_based_detection 已存在，跳过迁移")
                return
            
            # 添加新字段
            alter_sql = text("""
                ALTER TABLE system_settings
                ADD COLUMN enable_rule_based_detection BOOLEAN DEFAULT FALSE COMMENT '是否启用规则检测（BERT + 规则混合检测）'
            """)
            
            await session.execute(alter_sql)
            await session.commit()
            print("✅ 成功添加字段 enable_rule_based_detection")
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(migrate())