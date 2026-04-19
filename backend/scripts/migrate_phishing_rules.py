"""创建钓鱼检测规则表"""

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
    """创建钓鱼检测规则表"""
    config = AppConfigLoader().load()
    db_manager = DatabaseManager(config.get_database_url())
    
    try:
        async with db_manager.get_session() as session:
            # 检查表是否已存在
            check_sql = text("""
                SELECT COUNT(*) as count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = :db_name
                AND TABLE_NAME = 'phishing_rules'
            """)
            
            result = await session.execute(check_sql, {"db_name": config.db_name})
            count = result.scalar()
            
            if count > 0:
                print("表 phishing_rules 已存在，跳过迁移")
                return
            
            # 创建表
            create_sql = text("""
                CREATE TABLE phishing_rules (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                    rule_name VARCHAR(100) NOT NULL COMMENT '规则名称',
                    rule_type VARCHAR(20) NOT NULL COMMENT '规则类型：URL/SENDER/CONTENT/STRUCTURE',
                    rule_pattern TEXT NOT NULL COMMENT '规则模式（正则表达式或关键词）',
                    rule_description TEXT COMMENT '规则描述',
                    severity INT DEFAULT 5 COMMENT '规则严重程度（1-10）',
                    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_rule_type (rule_type),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='钓鱼检测规则表'
            """)
            
            await session.execute(create_sql)
            await session.commit()
            print("✅ 成功创建表 phishing_rules")
            
            # 插入默认规则
            default_rules = [
                {
                    "rule_name": "紧急性词汇检测",
                    "rule_type": "CONTENT",
                    "rule_pattern": r"(立即|紧急|马上|最后机会|即将过期|马上处理)",
                    "rule_description": "检测邮件中的紧急性词汇，钓鱼邮件常使用此类词汇制造紧迫感",
                    "severity": 6,
                },
                {
                    "rule_name": "敏感操作词汇检测",
                    "rule_type": "CONTENT",
                    "rule_pattern": r"(验证|登录|密码|账户|银行卡|身份证|手机号|验证码)",
                    "rule_description": "检测邮件中的敏感操作词汇，钓鱼邮件常要求用户执行敏感操作",
                    "severity": 7,
                },
                {
                    "rule_name": "威胁性词汇检测",
                    "rule_type": "CONTENT",
                    "rule_pattern": r"(账户将被冻结|账户将被删除|账户将被暂停|将会受到法律制裁)",
                    "rule_description": "检测邮件中的威胁性词汇，钓鱼邮件常使用威胁手段",
                    "severity": 8,
                },
                {
                    "rule_name": "IP地址链接检测",
                    "rule_type": "URL",
                    "rule_pattern": r"https?://(\d{1,3}\.){3}\d{1,3}",
                    "rule_description": "检测IP地址形式的链接，钓鱼邮件常使用IP地址隐藏真实域名",
                    "severity": 9,
                },
                {
                    "rule_name": "短链接服务检测",
                    "rule_type": "URL",
                    "rule_pattern": r"https?://(bit\.ly|tinyurl\.com|goo\.gl|t\.co|ow\.ly|is\.gd)",
                    "rule_description": "检测短链接服务，钓鱼邮件常使用短链接隐藏真实URL",
                    "severity": 6,
                },
                {
                    "rule_name": "可疑域名后缀检测",
                    "rule_type": "URL",
                    "rule_pattern": r"\.(xyz|top|gq|tk|ml|cf|ga|pw)",
                    "rule_description": "检测可疑的域名后缀，这些域名常被用于钓鱼攻击",
                    "severity": 7,
                },
                {
                    "rule_name": "免费邮箱发件人检测",
                    "rule_type": "SENDER",
                    "rule_pattern": r"@(gmail\.com|163\.com|qq\.com|hotmail\.com|outlook\.com)",
                    "rule_description": "检测免费邮箱发件人，重要服务通常不会使用免费邮箱",
                    "severity": 5,
                },
                {
                    "rule_name": "发件人格式异常检测",
                    "rule_type": "SENDER",
                    "rule_pattern": r".*<.*>.*<.*>.*",
                    "rule_description": "检测发件人格式异常，如包含多个尖括号",
                    "severity": 6,
                },
            ]
            
            for rule in default_rules:
                insert_sql = text("""
                    INSERT INTO phishing_rules 
                    (rule_name, rule_type, rule_pattern, rule_description, severity)
                    VALUES (:rule_name, :rule_type, :rule_pattern, :rule_description, :severity)
                """)
                await session.execute(insert_sql, rule)
            
            await session.commit()
            print(f"✅ 成功插入 {len(default_rules)} 条默认规则")
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(migrate())