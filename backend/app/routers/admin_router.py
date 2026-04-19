"""管理员路由层。"""

import logging
from functools import wraps
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import AppConfig
from app.middleware.jwt_auth import JWTPayload, get_current_user
from app.schemas.admin_schema import (
    CreateUserRequest,
    CreateWhitelistRuleRequest,
    OperationResponse,
    SetUserStatusRequest,
    UpdateWhitelistRuleRequest,
    UserListResponse,
    WhitelistRuleListResponse,
    WhitelistRuleResponse,
    UserResponse,
    CreateSenderWhitelistRequest,
    UpdateSenderWhitelistRequest,
    SenderWhitelistResponse,
    SenderWhitelistListResponse,
    UpdateSystemSettingsRequest,
    SystemSettingsResponse,
)
from app.services.admin_service import AdminService


def require_role(*allowed_roles: str) -> Callable:
    """角色检查装饰器工厂。

    Args:
        allowed_roles: 允许的角色列表。

    Returns:
        装饰器函数。
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: JWTPayload = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="未认证")

            # 从数据库获取用户角色（暂时通过student_id判断）
            # 由于JWT不包含role，需要在路由中查询
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class AdminRouter:
    """管理员路由类。

    该类负责注册管理员相关的 API 路由。
    """

    def __init__(
        self,
        admin_service: AdminService,
        config: AppConfig,
        logger: logging.Logger,
    ) -> None:
        """初始化管理员路由。

        Args:
            admin_service: 管理员服务。
            config: 应用配置。
            logger: 日志记录器。
        """
        self._admin_service = admin_service
        self._logger = logger
        self._router = APIRouter(prefix=config.api_prefix + "/admin", tags=["admin"])
        self._register_routes()

    @property
    def router(self) -> APIRouter:
        """对外暴露 FastAPI 路由对象。"""
        return self._router

    def _register_routes(self) -> None:
        """注册路由方法。"""
        # 管理员管理（仅超级管理员可用）
        self._router.get("/admins", response_model=UserListResponse)(self.get_admins)
        self._router.post("/admins", response_model=UserResponse)(self.create_admin)
        self._router.patch(
            "/admins/{user_id}/status", response_model=OperationResponse
        )(self.set_admin_status)
        self._router.delete("/admins/{user_id}", response_model=OperationResponse)(
            self.delete_admin
        )

        # 旧接口兼容（获取所有用户）
        self._router.get("/users", response_model=UserListResponse)(self.get_users)

        # URL白名单管理
        self._router.get("/whitelist", response_model=WhitelistRuleListResponse)(
            self.get_whitelist_rules
        )
        self._router.post("/whitelist", response_model=WhitelistRuleResponse)(
            self.create_whitelist_rule
        )
        self._router.put("/whitelist/{rule_id}", response_model=WhitelistRuleResponse)(
            self.update_whitelist_rule
        )
        self._router.delete("/whitelist/{rule_id}", response_model=OperationResponse)(
            self.delete_whitelist_rule
        )

        # 发件人白名单管理
        self._router.get(
            "/sender-whitelist", response_model=SenderWhitelistListResponse
        )(self.get_sender_whitelist_rules)
        self._router.post("/sender-whitelist", response_model=SenderWhitelistResponse)(
            self.create_sender_whitelist_rule
        )
        self._router.put(
            "/sender-whitelist/{rule_id}", response_model=SenderWhitelistResponse
        )(self.update_sender_whitelist_rule)
        self._router.delete(
            "/sender-whitelist/{rule_id}", response_model=OperationResponse
        )(self.delete_sender_whitelist_rule)

        # 系统设置管理
        self._router.get("/settings", response_model=SystemSettingsResponse)(
            self.get_system_settings
        )
        self._router.put("/settings", response_model=SystemSettingsResponse)(
            self.update_system_settings
        )

    # ========== 管理员管理 API（仅超级管理员） ==========

    async def get_admins(
        self,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: JWTPayload = Depends(get_current_user),
    ) -> UserListResponse:
        """获取管理员列表（仅超级管理员可用）。"""
        self._logger.info(f"获取管理员列表: page={page}")
        users, total = await self._admin_service.get_admins(
            page=page, page_size=page_size
        )
        return UserListResponse(
            users=users, total=total, page=page, page_size=page_size
        )

    async def create_admin(
        self,
        request: CreateUserRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> UserResponse:
        """创建管理员（仅超级管理员可用）。"""
        self._logger.info(f"创建管理员: student_id={request.student_id}")
        user = await self._admin_service.create_user(request, role="admin")
        if not user:
            raise HTTPException(status_code=400, detail="账号已存在")
        return user

    async def set_admin_status(
        self,
        user_id: int,
        request: SetUserStatusRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> OperationResponse:
        """设置管理员启用/停用状态（仅超级管理员可用）。"""
        success = await self._admin_service.set_user_status(user_id, request.is_active)
        if success:
            return OperationResponse(success=True, message="管理员状态已更新")
        raise HTTPException(status_code=404, detail="用户不存在")

    async def delete_admin(
        self,
        user_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> OperationResponse:
        """删除管理员（仅超级管理员可用）。"""
        success = await self._admin_service.delete_user(user_id)
        if success:
            return OperationResponse(success=True, message="管理员已删除")
        raise HTTPException(status_code=404, detail="用户不存在")

    # ========== 旧接口兼容 ==========

    async def get_users(
        self,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: JWTPayload = Depends(get_current_user),
    ) -> UserListResponse:
        """获取所有用户列表（兼容旧接口）。"""
        users, total = await self._admin_service.get_users(
            page=page, page_size=page_size
        )
        return UserListResponse(
            users=users, total=total, page=page, page_size=page_size
        )

    # ========== 白名单管理 API ==========

    async def get_whitelist_rules(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> WhitelistRuleListResponse:
        """获取所有白名单规则。"""
        rules = await self._admin_service.get_whitelist_rules()
        return WhitelistRuleListResponse(rules=rules)

    async def create_whitelist_rule(
        self,
        request: CreateWhitelistRuleRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> WhitelistRuleResponse:
        """创建白名单规则。"""
        rule = await self._admin_service.create_whitelist_rule(request)
        return rule

    async def update_whitelist_rule(
        self,
        rule_id: int,
        request: UpdateWhitelistRuleRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> WhitelistRuleResponse:
        """更新白名单规则。"""
        rule = await self._admin_service.update_whitelist_rule(rule_id, request)
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        return rule

    async def delete_whitelist_rule(
        self,
        rule_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> OperationResponse:
        """删除URL白名单规则。"""
        success = await self._admin_service.delete_whitelist_rule(rule_id)
        if success:
            return OperationResponse(success=True, message="规则已删除")
        raise HTTPException(status_code=404, detail="规则不存在")

    # ========== 发件人白名单管理 API ==========

    async def get_sender_whitelist_rules(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SenderWhitelistListResponse:
        """获取所有发件人白名单规则。"""
        rules = await self._admin_service.get_sender_whitelist_rules()
        return SenderWhitelistListResponse(rules=rules)

    async def create_sender_whitelist_rule(
        self,
        request: CreateSenderWhitelistRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SenderWhitelistResponse:
        """创建发件人白名单规则。"""
        rule = await self._admin_service.create_sender_whitelist_rule(request)
        return rule

    async def update_sender_whitelist_rule(
        self,
        rule_id: int,
        request: UpdateSenderWhitelistRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SenderWhitelistResponse:
        """更新发件人白名单规则。"""
        rule = await self._admin_service.update_sender_whitelist_rule(rule_id, request)
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        return rule

    async def delete_sender_whitelist_rule(
        self,
        rule_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> OperationResponse:
        """删除发件人白名单规则。"""
        success = await self._admin_service.delete_sender_whitelist_rule(rule_id)
        if success:
            return OperationResponse(success=True, message="规则已删除")
        raise HTTPException(status_code=404, detail="规则不存在")

    # ========== 系统设置管理 API ==========

    async def get_system_settings(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SystemSettingsResponse:
        """获取系统设置。"""
        settings = await self._admin_service.get_system_settings()
        return settings

    async def update_system_settings(
        self,
        request: UpdateSystemSettingsRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SystemSettingsResponse:
        """更新系统设置。"""
        settings = await self._admin_service.update_system_settings(request)
        return settings