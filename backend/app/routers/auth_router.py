"""认证路由层。"""

import logging

from fastapi import APIRouter, Depends

from app.core.config import AppConfig
from app.middleware.jwt_auth import JWTPayload, get_current_user
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserInfoResponse,
)
from app.services.auth_service import AuthService


class AuthRouter:
    """认证路由类。

    该类负责注册认证相关的 API 路由。
    """

    def __init__(
        self,
        auth_service: AuthService,
        config: AppConfig,
        logger: logging.Logger,
    ) -> None:
        """初始化认证路由。

        Args:
            auth_service: 认证服务。
            config: 应用配置。
            logger: 日志记录器。
        """
        self._auth_service = auth_service
        self._logger = logger
        self._router = APIRouter(prefix=config.api_prefix, tags=["auth"])
        self._register_routes()

    @property
    def router(self) -> APIRouter:
        """对外暴露 FastAPI 路由对象。"""
        return self._router

    def _register_routes(self) -> None:
        """注册路由方法。"""
        self._router.post("/auth/login", response_model=LoginResponse)(self.login)
        self._router.post("/auth/refresh", response_model=RefreshTokenResponse)(
            self.refresh_token
        )
        self._router.get("/auth/me", response_model=UserInfoResponse)(self.get_me)

    async def login(self, request: LoginRequest) -> LoginResponse:
        """登录接口。

        Args:
            request: 登录请求数据。

        Returns:
            登录响应数据。
        """
        self._logger.info("收到登录请求 student_id=%s", request.student_id)
        return await self._auth_service.login(request)

    async def refresh_token(
        self, request: RefreshTokenRequest
    ) -> RefreshTokenResponse:
        """刷新令牌接口。

        Args:
            request: 刷新令牌请求数据。

        Returns:
            刷新令牌响应数据。
        """
        return await self._auth_service.refresh_token(request)

    async def get_me(
        self, current_user: JWTPayload = Depends(get_current_user)
    ) -> UserInfoResponse:
        """获取当前用户信息接口。

        Args:
            current_user: 当前认证用户信息。

        Returns:
            用户信息响应数据。
        """
        return UserInfoResponse(
            user_id=current_user.user_id,
            student_id=current_user.student_id,
            display_name=current_user.display_name,
        )
