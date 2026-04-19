"""邮箱账户路由层。"""

import logging

from fastapi import APIRouter, Depends

from app.core.config import AppConfig
from app.middleware.jwt_auth import JWTPayload, get_current_user
from app.schemas.email_account_schema import (
    AddEmailAccountRequest,
    AddEmailAccountResponse,
    EmailAccountListResponse,
    SyncEmailsResponse,
    DeleteEmailAccountResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.services.email_account_service import EmailAccountService


class EmailAccountRouter:
    """邮箱账户路由类。

    负责注册邮箱账户相关的 API 路由。
    """

    def __init__(
        self,
        email_account_service: EmailAccountService,
        config: AppConfig,
        logger: logging.Logger,
    ) -> None:
        """初始化邮箱账户路由。

        Args:
            email_account_service: 邮箱账户服务。
            config: 应用配置。
            logger: 日志记录器。
        """
        self._email_account_service = email_account_service
        self._logger = logger
        self._router = APIRouter(prefix=config.api_prefix, tags=["email-accounts"])
        self._register_routes()

    @property
    def router(self) -> APIRouter:
        """对外暴露 FastAPI 路由对象。"""
        return self._router

    def _register_routes(self) -> None:
        """注册路由方法。"""
        self._router.get("/email-accounts", response_model=EmailAccountListResponse)(
            self.get_email_accounts
        )
        self._router.post("/email-accounts", response_model=AddEmailAccountResponse)(
            self.add_email_account
        )
        self._router.delete(
            "/email-accounts/{account_id}", response_model=DeleteEmailAccountResponse
        )(self.delete_email_account)
        self._router.post("/email-accounts/{account_id}/sync", response_model=SyncEmailsResponse
        )(self.sync_emails)
        self._router.post("/email-accounts/sync-all")(self.sync_all_emails)
        self._router.post(
            "/email-accounts/test-connection", response_model=TestConnectionResponse
        )(self.test_connection)

    async def get_email_accounts(
        self, current_user: JWTPayload = Depends(get_current_user)
    ) -> EmailAccountListResponse:
        """获取邮箱账户列表。

        Args:
            current_user: 当前认证用户。

        Returns:
            邮箱账户列表响应。
        """
        self._logger.info("获取邮箱账户列表 user_id=%s", current_user.user_id)
        return await self._email_account_service.get_email_accounts(current_user.user_id)

    async def add_email_account(
        self,
        request: AddEmailAccountRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> AddEmailAccountResponse:
        """添加邮箱账户。

        Args:
            request: 添加邮箱请求。
            current_user: 当前认证用户。

        Returns:
            添加邮箱响应。
        """
        self._logger.info(
            "添加邮箱账户 user_id=%s, email=%s",
            current_user.user_id,
            request.email_address,
        )
        return await self._email_account_service.add_email_account(
            current_user.user_id, request
        )

    async def delete_email_account(
        self,
        account_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> DeleteEmailAccountResponse:
        """删除邮箱账户。

        Args:
            account_id: 邮箱账户ID。
            current_user: 当前认证用户。

        Returns:
            删除邮箱响应。
        """
        self._logger.info(
            "删除邮箱账户 user_id=%s, account_id=%s", current_user.user_id, account_id
        )
        return await self._email_account_service.delete_email_account(
            current_user.user_id, account_id
        )

    async def sync_emails(
        self,
        account_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SyncEmailsResponse:
        """同步邮箱邮件。

        Args:
            account_id: 邮箱账户ID。
            current_user: 当前认证用户。

        Returns:
            同步邮件响应。
        """
        self._logger.info(
            "同步邮件 user_id=%s, account_id=%s", current_user.user_id, account_id
        )
        return await self._email_account_service.sync_emails(
            current_user.user_id, account_id
        )

    async def sync_all_emails(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ):
        """同步用户所有邮箱账户的邮件。

        Args:
            current_user: 当前认证用户。

        Returns:
            同步结果。
        """
        self._logger.info("同步所有邮箱 user_id=%s", current_user.user_id)
        return await self._email_account_service.sync_all_emails(current_user.user_id)

    async def test_connection(
        self,
        request: TestConnectionRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> TestConnectionResponse:
        """测试邮箱连接。

        Args:
            request: 测试连接请求。
            current_user: 当前认证用户。

        Returns:
            测试连接响应。
        """
        self._logger.info("测试邮箱连接 email=%s", request.email_address)
        return await self._email_account_service.test_connection(request)