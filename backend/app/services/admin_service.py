"""管理员服务层。

提供管理员功能的业务逻辑，包括用户管理、URL白名单管理、发件人白名单管理和系统操作。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from app.crud.user_crud import UserCrud
from app.crud.email_crud import EmailCrud
from app.crud.url_whitelist_crud import UrlWhitelistCrud
from app.crud.sender_whitelist_crud import SenderWhitelistCrud
from app.services.system_settings_service import SystemSettingsService

if TYPE_CHECKING:
    from app.services.phishing_detection_service import PhishingDetectionService
from app.entities.user_entity import UserEntity
from app.entities.url_whitelist_entity import UrlWhitelistEntity
from app.entities.sender_whitelist_entity import SenderWhitelistEntity
from app.schemas.admin_schema import (
    CreateUserRequest,
    CreateWhitelistRuleRequest,
    UpdateWhitelistRuleRequest,
    UserResponse,
    WhitelistRuleResponse,
    CreateSenderWhitelistRequest,
    UpdateSenderWhitelistRequest,
    SenderWhitelistResponse,
    UpdateSystemSettingsRequest,
    SystemSettingsResponse,
)


class AdminService:
    """管理员服务类。

    整合用户管理、URL白名单管理和发件人白名单管理的业务逻辑。
    """

    def __init__(
        self,
        user_crud: UserCrud,
        whitelist_crud: UrlWhitelistCrud,
        sender_whitelist_crud: SenderWhitelistCrud,
        system_settings_service: SystemSettingsService,
        email_crud: Optional[EmailCrud],
        phishing_detection_service: Optional["PhishingDetectionService"],
        logger: logging.Logger,
    ) -> None:
        """初始化管理员服务。

        Args:
            user_crud: 用户CRUD实例。
            whitelist_crud: URL白名单CRUD实例。
            sender_whitelist_crud: 发件人白名单CRUD实例。
            system_settings_service: 系统设置服务。
            email_crud: 邮件CRUD实例（用于重新检测）。
            phishing_detection_service: 钓鱼检测服务（用于重新检测）。
            logger: 日志记录器。
        """
        self._user_crud = user_crud
        self._whitelist_crud = whitelist_crud
        self._sender_whitelist_crud = sender_whitelist_crud
        self._system_settings_service = system_settings_service
        self._email_crud = email_crud
        self._phishing_detection_service = phishing_detection_service
        self._logger = logger

    # ========== 用户管理 ==========

    async def get_users(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[List[UserResponse], int]:
        """获取用户列表。

        Args:
            page: 页码（从1开始）。
            page_size: 每页记录数。

        Returns:
            (用户响应列表, 总记录数) 元组。
        """
        skip = (page - 1) * page_size
        users, total = await self._user_crud.get_all_users(skip=skip, limit=page_size)

        user_responses = [
            UserResponse(
                id=user.id,
                student_id=user.student_id,
                display_name=user.display_name,
                is_active=user.is_active,
                role=user.role,
                created_at=user.created_at,
            )
            for user in users
        ]

        return user_responses, total

    async def get_students(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[List[UserResponse], int]:
        """获取学生用户列表。

        Args:
            page: 页码。
            page_size: 每页记录数。

        Returns:
            (学生用户列表, 总记录数) 元组。
        """
        skip = (page - 1) * page_size
        users, total = await self._user_crud.get_students(skip=skip, limit=page_size)

        user_responses = [
            UserResponse(
                id=user.id,
                student_id=user.student_id,
                display_name=user.display_name,
                is_active=user.is_active,
                role=user.role,
                created_at=user.created_at,
            )
            for user in users
        ]

        return user_responses, total

    async def get_admins(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[List[UserResponse], int]:
        """获取管理员列表（仅超级管理员可调用）。

        Args:
            page: 页码。
            page_size: 每页记录数。

        Returns:
            (管理员列表, 总记录数) 元组。
        """
        skip = (page - 1) * page_size
        users, total = await self._user_crud.get_admins(skip=skip, limit=page_size)

        user_responses = [
            UserResponse(
                id=user.id,
                student_id=user.student_id,
                display_name=user.display_name,
                is_active=user.is_active,
                role=user.role,
                created_at=user.created_at,
            )
            for user in users
        ]

        return user_responses, total

    async def create_user(
        self, request: CreateUserRequest, role: str = "user"
    ) -> Optional[UserResponse]:
        """创建新用户。

        Args:
            request: 创建用户请求。
            role: 用户角色（user/admin）。

        Returns:
            创建的用户响应，如果学号已存在返回None。
        """
        # 检查学号是否已存在
        existing = await self._user_crud.get_by_student_id(request.student_id)
        if existing:
            self._logger.warning(f"创建用户失败-学号已存在: {request.student_id}")
            return None

        user = await self._user_crud.create_with_role(
            student_id=request.student_id,
            password=request.password,
            display_name=request.display_name,
            role=role,
        )

        self._logger.info(f"创建用户成功: {request.student_id}, 角色: {role}")

        return UserResponse(
            id=user.id,
            student_id=user.student_id,
            display_name=user.display_name,
            is_active=user.is_active,
            role=user.role,
            created_at=user.created_at,
        )

    async def set_user_status(self, user_id: int, is_active: bool) -> bool:
        """设置用户启用/停用状态。

        Args:
            user_id: 用户ID。
            is_active: 是否启用。

        Returns:
            是否更新成功。
        """
        result = await self._user_crud.set_active_status(user_id, is_active)
        if result:
            self._logger.info(f"用户状态更新: user_id={user_id}, is_active={is_active}")
        return result

    async def delete_user(self, user_id: int) -> bool:
        """删除用户。

        Args:
            user_id: 用户ID。

        Returns:
            是否删除成功。
        """
        result = await self._user_crud.delete_user(user_id)
        if result:
            self._logger.info(f"删除用户: user_id={user_id}")
        return result

    # ========== 白名单管理 ==========

    async def get_whitelist_rules(self, user_id: Optional[int] = None) -> List[WhitelistRuleResponse]:
        """获取白名单规则。

        Args:
            user_id: 用户ID，如果为None则返回所有规则。

        Returns:
            白名单规则响应列表。
        """
        if user_id is not None:
            rules = await self._whitelist_crud.get_by_user_id(user_id)
        else:
            rules = await self._whitelist_crud.get_all()

        return [
            WhitelistRuleResponse(
                id=rule.id,
                rule_type=rule.rule_type,
                rule_value=rule.rule_value,
                description=rule.description,
                is_active=rule.is_active,
                created_at=rule.created_at,
            )
            for rule in rules
        ]

    async def create_whitelist_rule(
        self, request: CreateWhitelistRuleRequest, user_id: Optional[int] = None
    ) -> WhitelistRuleResponse:
        """创建白名单规则。

        Args:
            request: 创建规则请求。
            user_id: 用户ID，如果为None则创建全局规则。

        Returns:
            创建的规则响应。
        """
        rule = await self._whitelist_crud.create(
            rule_type=request.rule_type,
            rule_value=request.rule_value,
            description=request.description,
            user_id=user_id,
        )

        self._logger.info(f"创建白名单规则: {request.rule_type}:{request.rule_value}")

        return WhitelistRuleResponse(
            id=rule.id,
            rule_type=rule.rule_type,
            rule_value=rule.rule_value,
            description=rule.description,
            is_active=rule.is_active,
            created_at=rule.created_at,
        )

    async def update_whitelist_rule(
        self, rule_id: int, request: UpdateWhitelistRuleRequest
    ) -> Optional[WhitelistRuleResponse]:
        """更新白名单规则。

        Args:
            rule_id: 规则ID。
            request: 更新规则请求。

        Returns:
            更新后的规则响应，如果不存在返回None。
        """
        rule = await self._whitelist_crud.update(
            rule_id=rule_id,
            rule_type=request.rule_type,
            rule_value=request.rule_value,
            description=request.description,
            is_active=request.is_active,
        )

        if not rule:
            return None

        self._logger.info(f"更新白名单规则: rule_id={rule_id}")

        return WhitelistRuleResponse(
            id=rule.id,
            rule_type=rule.rule_type,
            rule_value=rule.rule_value,
            description=rule.description,
            is_active=rule.is_active,
            created_at=rule.created_at,
        )

    async def delete_whitelist_rule(self, rule_id: int, user_id: Optional[int] = None) -> bool:
        """删除URL白名单规则。

        Args:
            rule_id: 规则ID。
            user_id: 用户ID（用于权限验证）。

        Returns:
            是否删除成功。
        """
        result = await self._whitelist_crud.delete(rule_id, user_id)
        if result:
            self._logger.info(f"删除URL白名单规则: rule_id={rule_id}")
        return result

    # ========== 发件人白名单管理 ==========

    async def get_sender_whitelist_rules(self, user_id: Optional[int] = None) -> List[SenderWhitelistResponse]:
        """获取发件人白名单规则。

        Args:
            user_id: 用户ID，如果为None则返回所有规则。

        Returns:
            发件人白名单规则响应列表。
        """
        if user_id is not None:
            rules = await self._sender_whitelist_crud.get_by_user_id(user_id)
        else:
            rules = await self._sender_whitelist_crud.get_all()

        return [
            SenderWhitelistResponse(
                id=rule.id,
                rule_type=rule.rule_type,
                rule_value=rule.rule_value,
                description=rule.description,
                is_active=rule.is_active,
                created_at=rule.created_at,
            )
            for rule in rules
        ]

    async def create_sender_whitelist_rule(
        self, request: CreateSenderWhitelistRequest, user_id: Optional[int] = None
    ) -> SenderWhitelistResponse:
        """创建发件人白名单规则。

        Args:
            request: 创建规则请求。
            user_id: 用户ID，如果为None则创建全局规则。

        Returns:
            创建的规则响应。
        """
        rule = await self._sender_whitelist_crud.create(
            rule_type=request.rule_type,
            rule_value=request.rule_value,
            description=request.description,
            user_id=user_id,
        )

        self._logger.info(
            f"创建发件人白名单规则: {request.rule_type}:{request.rule_value}"
        )

        return SenderWhitelistResponse(
            id=rule.id,
            rule_type=rule.rule_type,
            rule_value=rule.rule_value,
            description=rule.description,
            is_active=rule.is_active,
            created_at=rule.created_at,
        )

    async def update_sender_whitelist_rule(
        self, rule_id: int, request: UpdateSenderWhitelistRequest
    ) -> Optional[SenderWhitelistResponse]:
        """更新发件人白名单规则。

        Args:
            rule_id: 规则ID。
            request: 更新规则请求。

        Returns:
            更新后的规则响应，如果不存在返回None。
        """
        rule = await self._sender_whitelist_crud.update(
            rule_id=rule_id,
            rule_type=request.rule_type,
            rule_value=request.rule_value,
            description=request.description,
            is_active=request.is_active,
        )

        if not rule:
            return None

        self._logger.info(f"更新发件人白名单规则: rule_id={rule_id}")

        return SenderWhitelistResponse(
            id=rule.id,
            rule_type=rule.rule_type,
            rule_value=rule.rule_value,
            description=rule.description,
            is_active=rule.is_active,
            created_at=rule.created_at,
        )

    async def delete_sender_whitelist_rule(self, rule_id: int, user_id: Optional[int] = None) -> bool:
        """删除发件人白名单规则。

        Args:
            rule_id: 规则ID。
            user_id: 用户ID（用于权限验证）。

        Returns:
            是否删除成功。
        """
        result = await self._sender_whitelist_crud.delete(rule_id, user_id)
        if result:
            self._logger.info(f"删除发件人白名单规则: rule_id={rule_id}")
        return result

    # ========== 系统设置管理 ==========

    async def get_system_settings(self) -> SystemSettingsResponse:
        """获取系统设置。

        Returns:
            系统设置响应。
        """
        settings = await self._system_settings_service.get_settings()
        return SystemSettingsResponse(
            enable_long_url_detection=settings.enable_long_url_detection,
            enable_rule_based_detection=settings.enable_rule_based_detection,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
        )

    async def update_system_settings(
        self, request: UpdateSystemSettingsRequest
    ) -> SystemSettingsResponse:
        """更新系统设置。

        Args:
            request: 更新系统设置请求。

        Returns:
            更新后的系统设置响应。
        """
        settings = await self._system_settings_service.update_settings(
            enable_long_url_detection=request.enable_long_url_detection,
            enable_rule_based_detection=request.enable_rule_based_detection,
        )
        return SystemSettingsResponse(
            enable_long_url_detection=settings.enable_long_url_detection,
            enable_rule_based_detection=settings.enable_rule_based_detection,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
        )