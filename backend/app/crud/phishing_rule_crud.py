"""钓鱼检测规则数据访问层。"""

from typing import List, Optional

from sqlalchemy import select

from app.core.database import DatabaseManager
from app.entities.phishing_rule_entity import PhishingRuleEntity
from app.utils.logging.crud_logger import CrudLogger


class PhishingRuleCrud:
    """钓鱼检测规则CRUD操作类。

    提供钓鱼检测规则的增删改查操作，使用异步数据库会话。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化钓鱼检测规则CRUD。

        Args:
            db_manager: 数据库管理器实例。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._crud_logger = crud_logger

    async def create(
        self,
        rule_name: str,
        rule_type: str,
        rule_pattern: str,
        rule_description: Optional[str] = None,
        severity: int = 5,
    ) -> PhishingRuleEntity:
        """创建钓鱼检测规则。

        Args:
            rule_name: 规则名称。
            rule_type: 规则类型（URL/SENDER/CONTENT/STRUCTURE）。
            rule_pattern: 规则模式（正则表达式或关键词）。
            rule_description: 规则描述。
            severity: 规则严重程度（1-10）。

        Returns:
            创建的钓鱼检测规则实体。
        """
        async with self._db_manager.get_session() as session:
            rule = PhishingRuleEntity(
                rule_name=rule_name,
                rule_type=rule_type,
                rule_pattern=rule_pattern,
                rule_description=rule_description,
                severity=severity,
            )
            session.add(rule)
            await session.flush()
            await session.refresh(rule)

            self._crud_logger.log_create(
                "创建钓鱼检测规则",
                {"rule_name": rule_name, "rule_type": rule_type},
            )

            return rule

    async def get_all(self, rule_type: Optional[str] = None) -> List[PhishingRuleEntity]:
        """获取所有钓鱼检测规则。

        Args:
            rule_type: 规则类型，如果为None则返回所有规则。

        Returns:
            钓鱼检测规则列表。
        """
        async with self._db_manager.get_session() as session:
            query = select(PhishingRuleEntity).order_by(
                PhishingRuleEntity.severity.desc(),
                PhishingRuleEntity.created_at.desc()
            )
            
            if rule_type is not None:
                query = query.where(PhishingRuleEntity.rule_type == rule_type)
            
            result = await session.execute(query)
            rules = list(result.scalars().all())

            self._crud_logger.log_read(
                "获取钓鱼检测规则",
                {"count": len(rules), "rule_type": rule_type},
            )

            return rules

    async def get_active_rules(self, rule_type: Optional[str] = None) -> List[PhishingRuleEntity]:
        """获取所有启用的钓鱼检测规则。

        Args:
            rule_type: 规则类型，如果为None则返回所有启用的规则。

        Returns:
            启用的钓鱼检测规则列表。
        """
        async with self._db_manager.get_session() as session:
            query = select(PhishingRuleEntity).where(
                PhishingRuleEntity.is_active == True
            ).order_by(
                PhishingRuleEntity.severity.desc(),
                PhishingRuleEntity.created_at.desc()
            )
            
            if rule_type is not None:
                query = query.where(PhishingRuleEntity.rule_type == rule_type)
            
            result = await session.execute(query)
            rules = list(result.scalars().all())

            self._crud_logger.log_read(
                "获取启用的钓鱼检测规则",
                {"count": len(rules), "rule_type": rule_type},
            )

            return rules

    async def get_by_id(self, rule_id: int) -> Optional[PhishingRuleEntity]:
        """根据ID获取钓鱼检测规则。

        Args:
            rule_id: 规则ID。

        Returns:
            钓鱼检测规则实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(PhishingRuleEntity).where(
                PhishingRuleEntity.id == rule_id
            )
            result = await session.execute(query)
            rule = result.scalar_one_or_none()

            self._crud_logger.log_read(
                "根据ID查询钓鱼检测规则",
                {"rule_id": rule_id, "found": rule is not None},
            )

            return rule

    async def update(
        self,
        rule_id: int,
        rule_name: Optional[str] = None,
        rule_type: Optional[str] = None,
        rule_pattern: Optional[str] = None,
        rule_description: Optional[str] = None,
        severity: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[PhishingRuleEntity]:
        """更新钓鱼检测规则。

        Args:
            rule_id: 规则ID。
            rule_name: 规则名称。
            rule_type: 规则类型。
            rule_pattern: 规则模式。
            rule_description: 规则描述。
            severity: 规则严重程度。
            is_active: 是否启用。

        Returns:
            更新后的规则实体，如果不存在返回None。
        """
        async with self._db_manager.get_session() as session:
            query = select(PhishingRuleEntity).where(
                PhishingRuleEntity.id == rule_id
            )
            result = await session.execute(query)
            rule = result.scalar_one_or_none()

            if not rule:
                self._crud_logger.log_update(
                    "更新钓鱼检测规则失败-规则不存在",
                    {"rule_id": rule_id, "success": False},
                )
                return None

            if rule_name is not None:
                rule.rule_name = rule_name
            if rule_type is not None:
                rule.rule_type = rule_type
            if rule_pattern is not None:
                rule.rule_pattern = rule_pattern
            if rule_description is not None:
                rule.rule_description = rule_description
            if severity is not None:
                rule.severity = severity
            if is_active is not None:
                rule.is_active = is_active

            await session.flush()
            await session.refresh(rule)

            self._crud_logger.log_update(
                "更新钓鱼检测规则",
                {"rule_id": rule_id, "success": True},
            )

            return rule

    async def delete(self, rule_id: int) -> bool:
        """删除钓鱼检测规则。

        Args:
            rule_id: 规则ID。

        Returns:
            是否删除成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(PhishingRuleEntity).where(
                PhishingRuleEntity.id == rule_id
            )
            result = await session.execute(query)
            rule = result.scalar_one_or_none()

            if not rule:
                self._crud_logger.log_delete(
                    "删除钓鱼检测规则失败-规则不存在",
                    {"rule_id": rule_id, "success": False},
                )
                return False

            await session.delete(rule)
            await session.flush()

            self._crud_logger.log_delete(
                "删除钓鱼检测规则",
                {"rule_id": rule_id, "success": True},
            )

            return True