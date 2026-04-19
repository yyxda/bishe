"""钓鱼检测路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
import asyncio
from typing import Optional

from app.middleware.jwt_auth import (
    get_current_user,
    get_optional_user,
    get_jwt_middleware,
    JWTPayload,
)
from app.schemas.phishing_schema import (
    VerifyLinkRequest,
    VerifyLinkResponse,
    PhishingStatsResponse,
    PhishingModelInfoResponse,
    PhishingReloadResponse,
)
from app.utils.phishing import PhishingDetectorInterface
from app.services.phishing_event_service import PhishingEventService


class PhishingRouter:
    """钓鱼检测路由。"""

    def __init__(
        self,
        phishing_detector: PhishingDetectorInterface,
        event_service: PhishingEventService,
    ) -> None:
        """初始化路由。

        Args:
            phishing_detector: 钓鱼检测器实例。
            event_service: 钓鱼检测事件推送服务。
        """
        self.router = APIRouter(prefix="/api/phishing", tags=["phishing"])
        self._phishing_detector = phishing_detector
        self._event_service = event_service
        self._register_routes()

    def _register_routes(self) -> None:
        """注册路由。"""
        self.router.post("/verify-link")(self.verify_link)
        self.router.get("/stats")(self.get_stats)
        self.router.get("/model-info")(self.get_model_info)
        self.router.post("/reload-model")(self.reload_model)
        self.router.get("/stream")(self.stream_events)

    async def verify_link(
        self,
        request: VerifyLinkRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> VerifyLinkResponse:
        """验证学号后返回链接。

        用户必须正确输入自己的学号才能获取高危链接内容。

        Args:
            request: 验证请求。
            current_user: 当前用户。

        Returns:
            验证结果。
        """
        if request.student_id != current_user.student_id:
            return VerifyLinkResponse(
                success=False,
                message="学号验证失败，请输入正确的学号。",
            )

        return VerifyLinkResponse(
            success=True,
            message="验证成功，请谨慎访问该链接。",
            link_url=request.link_url,
        )

    async def get_stats(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> PhishingStatsResponse:
        """获取钓鱼检测统计。

        Args:
            current_user: 当前用户。

        Returns:
            统计数据。
        """
        # TODO: 从数据库获取真实统计数据
        return PhishingStatsResponse(
            total_emails=0,
            normal_count=0,
            suspicious_count=0,
            high_risk_count=0,
        )

    async def get_model_info(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> PhishingModelInfoResponse:
        """获取钓鱼模型信息。

        Args:
            current_user: 当前用户。

        Returns:
            模型信息响应。
        """
        info = self._phishing_detector.get_model_info()
        return PhishingModelInfoResponse(success=True, model_info=info)

    async def reload_model(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> PhishingReloadResponse:
        """重载钓鱼模型。

        Args:
            current_user: 当前用户。

        Returns:
            重载结果响应。
        """
        success = await self._phishing_detector.reload_model()
        message = "模型重载成功。" if success else "模型重载失败，请检查日志。"
        return PhishingReloadResponse(success=success, message=message)

    async def stream_events(
        self,
        request: Request,
        token: Optional[str] = Query(default=None),
        current_user: Optional[JWTPayload] = Depends(get_optional_user),
    ) -> StreamingResponse:
        """SSE事件流，推送钓鱼检测结果更新。

        Args:
            request: FastAPI请求对象。
            token: JWT访问令牌（EventSource无法设置Header时使用）。
            current_user: 当前用户（可选）。

        Returns:
            SSE事件流响应。
        """
        if not current_user and token:
            current_user = get_jwt_middleware().verify_token(token)

        if not current_user:
            raise HTTPException(status_code=401, detail="未提供有效的认证令牌")

        queue = await self._event_service.register(current_user.user_id)

        async def event_generator():
            try:
                # 建立连接后发送一次确认事件
                yield "event: connected\ndata: {\"status\": \"ok\"}\n\n"
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=15)
                        yield message
                    except asyncio.TimeoutError:
                        # SSE保活，防止连接被中间件关闭
                        yield ": keep-alive\n\n"
            finally:
                await self._event_service.unregister(current_user.user_id, queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )
