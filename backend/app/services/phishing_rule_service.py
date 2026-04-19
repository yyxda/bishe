"""钓鱼检测规则服务层。"""

import logging
from typing import List, Optional

from app.crud.phishing_rule_crud import PhishingRuleCrud
from app.entities.phishing_rule_entity import PhishingRuleEntity
from app.schemas.phishing_rule_schema import (
    CreatePhishingRuleRequest,
    UpdatePhishingRuleRequest,
    PhishingRuleResponse,
)


class PhishingRuleService:
    """钓鱼检测规则服务类。

    提供钓鱼检测规则的业务逻辑。
    """

    def __init__(
        self,
        rule_crud: PhishingRuleCrud,
        logger: logging.Logger,
    ) -> None:
        """初始化钓鱼检测规则服务。

        Args:
            rule_crud: 钓鱼检测规则CRUD实例。
            logger: 日志记录器。
        """
        self._rule_crud = rule_crud
        self._logger = logger

    async def get_all_rules(
        self, rule_type: Optional[str] = None
    ) -> List[PhishingRuleResponse]:
        """获取所有钓鱼检测规则。

        Args:
            rule_type: 规则类型，如果为None则返回所有规则。

        Returns:
            钓鱼检测规则响应列表。
        """
        rules = await self._rule_crud.get_all(rule_type)

        return [
            PhishingRuleResponse(
                id=rule.id,
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                rule_pattern=rule.rule_pattern,
                rule_description=rule.rule_description,
                severity=rule.severity,
                is_active=rule.is_active,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
            )
            for rule in rules
        ]

    async def get_active_rules(
        self, rule_type: Optional[str] = None
    ) -> List[PhishingRuleEntity]:
        """获取所有启用的钓鱼检测规则。

        Args:
            rule_type: 规则类型，如果为None则返回所有启用的规则。

        Returns:
            启用的钓鱼检测规则实体列表。
        """
        return await self._rule_crud.get_active_rules(rule_type)

    async def create_rule(
        self, request: CreatePhishingRuleRequest
    ) -> PhishingRuleResponse:
        """创建钓鱼检测规则。

        Args:
            request: 创建规则请求。

        Returns:
            创建的规则响应。
        """
        rule = await self._rule_crud.create(
            rule_name=request.rule_name,
            rule_type=request.rule_type,
            rule_pattern=request.rule_pattern,
            rule_description=request.rule_description,
            severity=request.severity,
        )

        self._logger.info(
            f"创建钓鱼检测规则: {request.rule_name} ({request.rule_type})"
        )

        return PhishingRuleResponse(
            id=rule.id,
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            rule_pattern=rule.rule_pattern,
            rule_description=rule.rule_description,
            severity=rule.severity,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    async def update_rule(
        self, rule_id: int, request: UpdatePhishingRuleRequest
    ) -> Optional[PhishingRuleResponse]:
        """更新钓鱼检测规则。

        Args:
            rule_id: 规则ID。
            request: 更新规则请求。

        Returns:
            更新后的规则响应，如果不存在返回None。
        """
        rule = await self._rule_crud.update(
            rule_id=rule_id,
            rule_name=request.rule_name,
            rule_type=request.rule_type,
            rule_pattern=request.rule_pattern,
            rule_description=request.rule_description,
            severity=request.severity,
            is_active=request.is_active,
        )

        if not rule:
            return None

        self._logger.info(f"更新钓鱼检测规则: rule_id={rule_id}")

        return PhishingRuleResponse(
            id=rule.id,
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            rule_pattern=rule.rule_pattern,
            rule_description=rule.rule_description,
            severity=rule.severity,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )

    async def delete_rule(self, rule_id: int) -> bool:
        """删除钓鱼检测规则。

        Args:
            rule_id: 规则ID。

        Returns:
            是否删除成功。
        """
        result = await self._rule_crud.delete(rule_id)
        if result:
            self._logger.info(f"删除钓鱼检测规则: rule_id={rule_id}")
        return result