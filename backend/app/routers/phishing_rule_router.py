"""钓鱼检测规则路由层。"""

import logging
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query

from app.middleware.jwt_auth import JWTPayload, get_current_user
from app.schemas.phishing_rule_schema import (
    CreatePhishingRuleRequest,
    UpdatePhishingRuleRequest,
    PhishingRuleListResponse,
    PhishingRuleResponse,
)
from app.schemas.admin_schema import OperationResponse
from app.services.phishing_rule_service import PhishingRuleService


class PhishingRuleRouter:
    """钓鱼检测规则路由类。

    该类负责注册钓鱼检测规则相关的 API 路由。
    """

    def __init__(
        self,
        rule_service: PhishingRuleService,
        logger: logging.Logger,
    ) -> None:
        """初始化钓鱼检测规则路由。

        Args:
            rule_service: 钓鱼检测规则服务。
            logger: 日志记录器。
        """
        self._rule_service = rule_service
        self._logger = logger
        self._router = APIRouter(prefix="/api/phishing-rules", tags=["phishing-rules"])
        self._register_routes()

    @property
    def router(self) -> APIRouter:
        """对外暴露 FastAPI 路由对象。"""
        return self._router

    def _register_routes(self) -> None:
        """注册路由方法。"""
        self._router.get("", response_model=PhishingRuleListResponse)(
            self.get_rules
        )
        self._router.post("", response_model=PhishingRuleResponse)(
            self.create_rule
        )
        self._router.put("/{rule_id}", response_model=PhishingRuleResponse)(
            self.update_rule
        )
        self._router.delete("/{rule_id}", response_model=OperationResponse)(
            self.delete_rule
        )

    async def get_rules(
        self,
        rule_type: str = Query(None, description="规则类型过滤"),
        current_user: JWTPayload = Depends(get_current_user),
    ) -> PhishingRuleListResponse:
        """获取所有钓鱼检测规则。"""
        rules = await self._rule_service.get_all_rules(rule_type)
        return PhishingRuleListResponse(rules=rules, total=len(rules))

    async def create_rule(
        self,
        request: CreatePhishingRuleRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> PhishingRuleResponse:
        """创建钓鱼检测规则。"""
        rule = await self._rule_service.create_rule(request)
        return rule

    async def update_rule(
        self,
        rule_id: int,
        request: UpdatePhishingRuleRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> PhishingRuleResponse:
        """更新钓鱼检测规则。"""
        rule = await self._rule_service.update_rule(rule_id, request)
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        return rule

    async def delete_rule(
        self,
        rule_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> OperationResponse:
        """删除钓鱼检测规则。"""
        success = await self._rule_service.delete_rule(rule_id)
        if success:
            return OperationResponse(success=True, message="规则已删除")
        raise HTTPException(status_code=404, detail="规则不存在")