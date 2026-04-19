"""邮件路由层。"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.config import AppConfig
from app.middleware.jwt_auth import JWTPayload, get_current_user
from app.schemas.email_schema import (
    EmailListResponse,
    EmailDetailResponse,
    SendEmailRequest,
    SendEmailResponse,
    MarkAsReadResponse,
)
from app.schemas.admin_schema import (
    WhitelistRuleListResponse,
    WhitelistRuleResponse,
    CreateWhitelistRuleRequest,
    UpdateWhitelistRuleRequest,
    SenderWhitelistListResponse,
    SenderWhitelistResponse,
    CreateSenderWhitelistRequest,
    UpdateSenderWhitelistRequest,
    OperationResponse,
)
from app.services.email_service import EmailService
from app.services.phishing_detection_service import PhishingDetectionService
from app.services.admin_service import AdminService
from app.entities.email_account_entity import EmailAccountEntity


class EmailRouter:
    """邮件路由类。

    负责注册邮件相关的 API 路由。
    """

    def __init__(
        self,
        email_service: EmailService,
        phishing_detection_service: PhishingDetectionService,
        admin_service: AdminService,
        config: AppConfig,
        logger: logging.Logger,
    ) -> None:
        """初始化邮件路由。

        Args:
            email_service: 邮件服务。
            phishing_detection_service: 钓鱼检测服务。
            admin_service: 管理员服务（用于白名单管理）。
            config: 应用配置。
            logger: 日志记录器。
        """
        self._email_service = email_service
        self._phishing_detection_service = phishing_detection_service
        self._admin_service = admin_service
        self._logger = logger
        self._router = APIRouter(prefix=config.api_prefix, tags=["emails"])
        self._register_routes()

    @property
    def router(self) -> APIRouter:
        """对外暴露 FastAPI 路由对象。"""
        return self._router

    def _register_routes(self) -> None:
        """注册路由方法。"""
        self._router.get("/emails", response_model=EmailListResponse)(self.get_emails)
        self._router.get("/emails/{email_id}", response_model=EmailDetailResponse)(
            self.get_email_detail
        )
        self._router.post("/emails/send", response_model=SendEmailResponse)(
            self.send_email
        )
        self._router.post("/emails/{email_id}/read", response_model=MarkAsReadResponse)(
            self.mark_as_read
        )
        self._router.post("/emails/detect-pending")(self.detect_pending_emails)
        self._router.post("/emails/redetect")(self.redetect_emails)

        # 白名单管理（学生用户可访问）
        self._router.get("/whitelist", response_model=WhitelistRuleListResponse)(
            self.get_whitelist_rules
        )
        self._router.post("/whitelist", response_model=WhitelistRuleResponse)(
            self.create_whitelist_rule
        )
        self._router.delete("/whitelist/{rule_id}", response_model=OperationResponse)(
            self.delete_whitelist_rule
        )
        self._router.get("/sender-whitelist", response_model=SenderWhitelistListResponse)(
            self.get_sender_whitelist_rules
        )
        self._router.post("/sender-whitelist", response_model=SenderWhitelistResponse)(
            self.create_sender_whitelist_rule
        )
        self._router.delete("/sender-whitelist/{rule_id}", response_model=OperationResponse)(
            self.delete_sender_whitelist_rule
        )

    async def get_emails(
        self,
        current_user: JWTPayload = Depends(get_current_user),
        account_id: Optional[int] = Query(default=None, description="邮箱账户ID"),
        mailbox_id: Optional[int] = Query(default=None, description="文件夹ID"),
        folder: Optional[str] = Query(default=None, description="邮件文件夹: inbox(收件箱), phishing(钓鱼邮件)"),
        limit: int = Query(default=1000, ge=1, le=10000, description="返回数量"),
        offset: int = Query(default=0, ge=0, description="偏移量"),
    ) -> EmailListResponse:
        """获取邮件列表。

        Args:
            current_user: 当前认证用户。
            account_id: 邮箱账户ID（可选）。
            mailbox_id: 文件夹ID（可选）。
            folder: 邮件文件夹（inbox: 收件箱, phishing: 钓鱼邮件）。
            limit: 返回数量限制。
            offset: 偏移量。

        Returns:
            邮件列表响应。
        """
        self._logger.info(
            "获取邮件列表 user_id=%s, account_id=%s, mailbox_id=%s, folder=%s",
            current_user.user_id,
            account_id,
            mailbox_id,
            folder,
        )
        return await self._email_service.get_emails(
            current_user.user_id, account_id, mailbox_id, folder, limit, offset
        )

    async def get_email_detail(
        self,
        email_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> EmailDetailResponse:
        """获取邮件详情。

        Args:
            email_id: 邮件ID。
            current_user: 当前认证用户。

        Returns:
            邮件详情响应。
        """
        self._logger.info(
            "获取邮件详情 user_id=%s, email_id=%s", current_user.user_id, email_id
        )
        return await self._email_service.get_email_detail(current_user.user_id, email_id)

    async def send_email(
        self,
        request: SendEmailRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SendEmailResponse:
        """发送邮件。

        Args:
            request: 发送邮件请求。
            current_user: 当前认证用户。

        Returns:
            发送邮件响应。
        """
        self._logger.info(
            "发送邮件 user_id=%s, to=%s", current_user.user_id, request.to_addresses
        )
        return await self._email_service.send_email(current_user.user_id, request)

    async def mark_as_read(
        self,
        email_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> MarkAsReadResponse:
        """标记邮件为已读。

        Args:
            email_id: 邮件ID。
            current_user: 当前认证用户。

        Returns:
            标记已读响应。
        """
        self._logger.info(
            "标记邮件已读 user_id=%s, email_id=%s", current_user.user_id, email_id
        )
        return await self._email_service.mark_as_read(current_user.user_id, email_id)

    async def detect_pending_emails(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> dict:
        """检测所有待检测的邮件。

        Args:
            current_user: 当前认证用户。

        Returns:
            检测结果。
        """
        from app.entities.email_entity import MailboxMessage, PhishingStatus
        from sqlalchemy import select
        
        # 查询所有PENDING状态的邮件
        query = select(MailboxMessage.id).where(
            MailboxMessage.phishing_status == PhishingStatus.PENDING
        )
        result = await self._email_service._email_crud._db_manager.session.execute(query)
        email_ids = result.scalars().all()
        
        if not email_ids:
            return {"success": True, "message": "没有待检测的邮件", "count": 0}
        
        self._logger.info(
            "手动触发检测待检测邮件: user_id=%s, count=%d",
            current_user.user_id,
            len(email_ids),
        )
        
        # 启动后台检测任务
        await self._phishing_detection_service.detect_emails_async(list(email_ids))
        
        return {
            "success": True,
            "message": f"已启动{len(email_ids)}封邮件的检测任务",
            "count": len(email_ids)
        }

    async def redetect_emails(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> dict:
        """重新检测当前用户的所有邮件。

        Args:
            current_user: 当前认证用户。

        Returns:
            检测结果。
        """
        from app.entities.mailbox_message_entity import MailboxMessageEntity
        from app.entities.email_entity import EmailEntity
        from sqlalchemy import select
        
        # 查询当前用户的所有邮箱账户ID
        async with self._email_service._email_crud._db_manager.get_session() as session:
            account_query = select(EmailAccountEntity.id).where(
                EmailAccountEntity.user_id == current_user.user_id
            )
            account_result = await session.execute(account_query)
            account_ids = [row[0] for row in account_result.fetchall()]
            
            if not account_ids:
                return {"success": True, "message": "没有邮箱账户", "count": 0}
            
            # 查询这些账户的所有邮件
            query = select(MailboxMessageEntity.id).join(
                MailboxMessageEntity.message
            ).where(
                EmailEntity.email_account_id.in_(account_ids)
            )
            result = await session.execute(query)
            email_ids = result.scalars().all()
        
        if not email_ids:
            return {"success": True, "message": "没有邮件需要重新检测", "count": 0}
        
        self._logger.info(
            "用户重新检测邮件: user_id=%s, count=%d",
            current_user.user_id,
            len(email_ids),
        )
        
        # 启动后台检测任务
        await self._phishing_detection_service.detect_emails_async(list(email_ids))
        
        return {
            "success": True,
            "message": f"已启动{len(email_ids)}封邮件的重新检测任务",
            "count": len(email_ids)
        }

    # ========== 白名单管理 API（学生用户可访问） ==========

    async def get_whitelist_rules(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> WhitelistRuleListResponse:
        """获取URL白名单规则。"""
        rules = await self._admin_service.get_whitelist_rules(current_user.user_id)
        return WhitelistRuleListResponse(rules=rules)

    async def create_whitelist_rule(
        self,
        request: CreateWhitelistRuleRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> WhitelistRuleResponse:
        """创建URL白名单规则。"""
        rule = await self._admin_service.create_whitelist_rule(request, current_user.user_id)
        return rule

    async def delete_whitelist_rule(
        self,
        rule_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> OperationResponse:
        """删除URL白名单规则。"""
        success = await self._admin_service.delete_whitelist_rule(rule_id, current_user.user_id)
        if success:
            return OperationResponse(success=True, message="规则已删除")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="规则不存在")

    async def get_sender_whitelist_rules(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SenderWhitelistListResponse:
        """获取发件人白名单规则。"""
        rules = await self._admin_service.get_sender_whitelist_rules(current_user.user_id)
        return SenderWhitelistListResponse(rules=rules)

    async def create_sender_whitelist_rule(
        self,
        request: CreateSenderWhitelistRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> SenderWhitelistResponse:
        """创建发件人白名单规则。"""
        rule = await self._admin_service.create_sender_whitelist_rule(request, current_user.user_id)
        return rule

    async def delete_sender_whitelist_rule(
        self,
        rule_id: int,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> OperationResponse:
        """删除发件人白名单规则。"""
        success = await self._admin_service.delete_sender_whitelist_rule(rule_id, current_user.user_id)
        if success:
            return OperationResponse(success=True, message="规则已删除")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="规则不存在")