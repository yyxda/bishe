"""白名单管理工具。

帮助管理员快速添加发件人和URL白名单，降低误报率。
"""

import asyncio
import logging
from pathlib import Path
import sys

# 添加项目根目录到路径
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.core.config import AppConfigLoader
from app.core.database import DatabaseManager
from app.crud.url_whitelist_crud import UrlWhitelistCrud
from app.crud.sender_whitelist_crud import SenderWhitelistCrud
from app.utils.logging.logger_factory import LoggerFactory
from app.utils.logging.crud_logger import CrudLogger


class WhitelistManager:
    """白名单管理器。"""

    # 推荐添加到白名单的发件人域名
    RECOMMENDED_SENDER_DOMAINS = [
        "@qq.com",
        "@163.com",
        "@126.com",
        "@sina.com.cn",
        "@sohu.com",
        "@gmail.com",
        "@outlook.com",
        "@hotmail.com",
        "@hhstu.edu.cn",
        "@edu.cn",
    ]

    # 推荐添加到白名单的URL域名
    RECOMMENDED_URL_DOMAINS = [
        "qq.com",
        "163.com",
        "126.com",
        "sina.com.cn",
        "sohu.com",
        "baidu.com",
        "weixin.qq.com",
        "mp.weixin.qq.com",
        "zhihu.com",
        "csdn.net",
        "github.com",
        "gitee.com",
        "hhstu.edu.cn",
        "edu.cn",
    ]

    def __init__(self, db_manager: DatabaseManager, logger: logging.Logger):
        """初始化白名单管理器。

        Args:
            db_manager: 数据库管理器。
            logger: 日志记录器。
        """
        self._db_manager = db_manager
        self._logger = logger

        # 初始化CRUD
        crud_logger_factory = LoggerFactory()
        url_whitelist_logger = crud_logger_factory.create_crud_logger(
            "app.crud.url_whitelist", "URL白名单"
        )
        sender_whitelist_logger = crud_logger_factory.create_crud_logger(
            "app.crud.sender_whitelist", "发件人白名单"
        )

        self._url_whitelist_crud = UrlWhitelistCrud(
            db_manager, url_whitelist_logger
        )
        self._sender_whitelist_crud = SenderWhitelistCrud(
            db_manager, sender_whitelist_logger
        )

    async def add_recommended_whitelists(self) -> dict:
        """添加推荐的白名单。

        Returns:
            添加结果统计。
        """
        results = {
            "url_whitelist": {"added": 0, "skipped": 0},
            "sender_whitelist": {"added": 0, "skipped": 0},
        }

        # 添加URL白名单
        for domain in self.RECOMMENDED_URL_DOMAINS:
            try:
                existing = await self._url_whitelist_crud.get_by_domain(domain)
                if existing:
                    results["url_whitelist"]["skipped"] += 1
                    self._logger.info(f"URL白名单已存在: {domain}")
                else:
                    await self._url_whitelist_crud.create(
                        domain=domain,
                        description="常用正常网站",
                        added_by="system"
                    )
                    results["url_whitelist"]["added"] += 1
                    self._logger.info(f"已添加URL白名单: {domain}")
            except Exception as e:
                self._logger.error(f"添加URL白名单失败 {domain}: {e}")

        # 添加发件人白名单
        for domain in self.RECOMMENDED_SENDER_DOMAINS:
            try:
                existing = await self._sender_whitelist_crud.get_by_sender(domain)
                if existing:
                    results["sender_whitelist"]["skipped"] += 1
                    self._logger.info(f"发件人白名单已存在: {domain}")
                else:
                    await self._sender_whitelist_crud.create(
                        sender=domain,
                        description="常用邮箱域名",
                        added_by="system"
                    )
                    results["sender_whitelist"]["added"] += 1
                    self._logger.info(f"已添加发件人白名单: {domain}")
            except Exception as e:
                self._logger.error(f"添加发件人白名单失败 {domain}: {e}")

        return results

    async def add_sender_whitelist(self, sender: str, description: str = "") -> bool:
        """添加发件人白名单。

        Args:
            sender: 发件人地址或域名。
            description: 描述。

        Returns:
            是否添加成功。
        """
        try:
            existing = await self._sender_whitelist_crud.get_by_sender(sender)
            if existing:
                self._logger.warning(f"发件人白名单已存在: {sender}")
                return False

            await self._sender_whitelist_crud.create(
                sender=sender,
                description=description,
                added_by="admin"
            )
            self._logger.info(f"已添加发件人白名单: {sender}")
            return True
        except Exception as e:
            self._logger.error(f"添加发件人白名单失败 {sender}: {e}")
            return False

    async def add_url_whitelist(self, domain: str, description: str = "") -> bool:
        """添加URL白名单。

        Args:
            domain: URL域名。
            description: 描述。

        Returns:
            是否添加成功。
        """
        try:
            existing = await self._url_whitelist_crud.get_by_domain(domain)
            if existing:
                self._logger.warning(f"URL白名单已存在: {domain}")
                return False

            await self._url_whitelist_crud.create(
                domain=domain,
                description=description,
                added_by="admin"
            )
            self._logger.info(f"已添加URL白名单: {domain}")
            return True
        except Exception as e:
            self._logger.error(f"添加URL白名单失败 {domain}: {e}")
            return False

    async def list_whitelists(self) -> dict:
        """列出所有白名单。

        Returns:
            白名单列表。
        """
        url_whitelists = await self._url_whitelist_crud.get_all()
        sender_whitelists = await self._sender_whitelist_crud.get_all()

        return {
            "url_whitelists": [
                {
                    "id": w.id,
                    "domain": w.domain,
                    "description": w.description,
                    "added_by": w.added_by,
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                }
                for w in url_whitelists
            ],
            "sender_whitelists": [
                {
                    "id": w.id,
                    "sender": w.sender,
                    "description": w.description,
                    "added_by": w.added_by,
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                }
                for w in sender_whitelists
            ],
        }

    async def clear_all_whitelists(self) -> dict:
        """清空所有白名单。

        Returns:
            删除结果统计。
        """
        results = {
            "url_whitelist": 0,
            "sender_whitelist": 0,
        }

        try:
            url_whitelists = await self._url_whitelist_crud.get_all()
            for w in url_whitelists:
                await self._url_whitelist_crud.delete(w.id)
                results["url_whitelist"] += 1
        except Exception as e:
            self._logger.error(f"清空URL白名单失败: {e}")

        try:
            sender_whitelists = await self._sender_whitelist_crud.get_all()
            for w in sender_whitelists:
                await self._sender_whitelist_crud.delete(w.id)
                results["sender_whitelist"] += 1
        except Exception as e:
            self._logger.error(f"清空发件人白名单失败: {e}")

        return results


async def main():
    """主函数。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger("whitelist_manager")

    # 加载配置
    config = AppConfigLoader().load()

    # 创建数据库管理器
    db_manager = DatabaseManager(config.get_database_url())

    try:
        # 创建白名单管理器
        manager = WhitelistManager(db_manager, logger)

        # 添加推荐的白名单
        print("\n" + "=" * 60)
        print("开始添加推荐的白名单...")
        print("=" * 60 + "\n")

        results = await manager.add_recommended_whitelists()

        print("\n" + "=" * 60)
        print("添加完成！")
        print("=" * 60)
        print(f"\nURL白名单:")
        print(f"  - 新增: {results['url_whitelist']['added']}")
        print(f"  - 跳过: {results['url_whitelist']['skipped']}")
        print(f"\n发件人白名单:")
        print(f"  - 新增: {results['sender_whitelist']['added']}")
        print(f"  - 跳过: {results['sender_whitelist']['skipped']}")

        # 列出所有白名单
        print("\n" + "=" * 60)
        print("当前白名单列表:")
        print("=" * 60 + "\n")

        whitelists = await manager.list_whitelists()

        print("URL白名单:")
        for w in whitelists["url_whitelists"]:
            print(f"  - {w['domain']} ({w['description']})")

        print(f"\n发件人白名单:")
        for w in whitelists["sender_whitelists"]:
            print(f"  - {w['sender']} ({w['description']})")

        print("\n" + "=" * 60)
        print("✅ 白名单初始化完成！")
        print("=" * 60 + "\n")

    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())