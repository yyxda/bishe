"""钓鱼邮件异步检测服务。

负责后台异步检测邮件，并实时更新检测结果。
支持发件人白名单和URL白名单机制。
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from app.crud.email_crud import EmailCrud
from app.entities.email_entity import PhishingLevel, PhishingStatus
from app.utils.phishing import PhishingDetectorInterface
from app.utils.phishing.phishing_detector_interface import (
    PhishingResult,
    PhishingLevel as DetectorPhishingLevel,
)
from app.services.phishing_event_service import PhishingEventService
from app.services.url_whitelist_service import UrlWhitelistMatcher
from app.services.sender_whitelist_service import SenderWhitelistMatcher
from app.services.system_settings_service import SystemSettingsService


class PhishingDetectionService:
    """钓鱼检测服务。

    提供后台异步检测功能，避免阻塞用户操作。
    支持发件人白名单和URL白名单机制：
    - 发件人在白名单中：直接判断为正常邮件，置信度为0
    - 所有URL都在白名单中：直接判断为正常邮件，置信度为0
    """

    def __init__(
        self,
        email_crud: EmailCrud,
        phishing_detector: PhishingDetectorInterface,
        event_service: Optional[PhishingEventService],
        url_whitelist_matcher: Optional[UrlWhitelistMatcher],
        sender_whitelist_matcher: Optional[SenderWhitelistMatcher],
        logger: logging.Logger,
        system_settings_service: Optional[SystemSettingsService] = None,
        rule_based_detector=None,
    ):
        """初始化钓鱼检测服务。

        Args:
            email_crud: 邮件数据访问对象。
            phishing_detector: 钓鱼检测器。
            event_service: 钓鱼检测事件推送服务。
            url_whitelist_matcher: URL白名单匹配器。
            sender_whitelist_matcher: 发件人白名单匹配器。
            logger: 日志记录器。
            system_settings_service: 系统设置服务（用于获取规则检测开关）。
            rule_based_detector: 规则检测器（用于混合检测）。
        """
        self._email_crud = email_crud
        self._phishing_detector = phishing_detector
        self._event_service = event_service
        self._url_whitelist_matcher = url_whitelist_matcher
        self._sender_whitelist_matcher = sender_whitelist_matcher
        self._logger = logger
        self._system_settings_service = system_settings_service
        self._rule_based_detector = rule_based_detector
        self._detection_tasks: Dict[int, asyncio.Task] = {}  # 跟踪正在运行的检测任务

    async def detect_emails_async(
        self,
        email_ids: List[int],
        callback: Optional[callable] = None,
    ) -> None:
        """异步检测邮件列表。

        在后台检测邮件，不阻塞主流程。每检测完一封邮件，立即更新数据库。

        Args:
            email_ids: 要检测的邮件ID列表。
            callback: 可选的回调函数，每检测完一封邮件时调用 callback(email_id, result)
        """
        task = asyncio.create_task(self._detect_and_update_batch(email_ids, callback))
        # 不await，让任务在后台运行
        self._logger.info(f"启动后台检测任务，共 {len(email_ids)} 封邮件")

    async def _detect_and_update_batch(
        self,
        email_ids: List[int],
        callback: Optional[callable] = None,
    ) -> None:
        """批量检测并更新邮件（后台任务）。

        Args:
            email_ids: 要检测的邮件ID列表。
            callback: 回调函数。
        """
        user_ids: Set[int] = set()
        try:
            for email_id in email_ids:
                try:
                    user_id = await self._detect_and_update_single(email_id, callback)
                    if user_id:
                        user_ids.add(user_id)
                except Exception as e:
                    self._logger.error(
                        f"检测邮件 {email_id} 失败: {str(e)}", exc_info=True
                    )
        finally:
            self._logger.info(f"后台检测任务完成，共处理 {len(email_ids)} 封邮件")
            await self._notify_batch_completed(user_ids, len(email_ids))

    async def _detect_and_update_single(
        self,
        email_id: int,
        callback: Optional[callable] = None,
    ) -> Optional[int]:
        """检测并更新单封邮件。

        检测顺序：
        1. 检查发件人是否在白名单中
        2. 检查所有URL是否都在白名单中
        3. 如果都不在白名单，执行正常检测

        Args:
            email_id: 邮件ID。
            callback: 回调函数。

        Returns:
            对应的用户ID，失败返回None。
        """
        # 获取邮件详情
        mailbox_message = await self._email_crud.get_by_id(email_id)
        if not mailbox_message or not mailbox_message.message:
            self._logger.warning(f"邮件 {email_id} 不存在，跳过检测")
            return None

        message = mailbox_message.message
        body = message.body
        user_id = message.email_account.user_id if message.email_account else None

        sender_address = message.sender_address or ""
        content_html = body.content_html if body else None

        # 检查白名单
        result = await self._check_whitelist_and_detect(
            sender=sender_address,
            subject=message.subject,
            content_text=body.content_text if body else None,
            content_html=content_html,
            user_id=user_id,
        )

        # 更新数据库
        phishing_level = self._map_phishing_level(result.level.value)
        await self._email_crud.update_phishing_result(
            message_id=message.id,
            phishing_level=phishing_level,
            phishing_score=result.score,
            phishing_reason=result.reason,
            phishing_status=PhishingStatus.COMPLETED,
        )

        self._logger.debug(
            f"邮件 {email_id} 检测完成: level={result.level.value}, score={result.score}"
        )

        # 调用回调函数（用于实时推送）
        if callback:
            try:
                await callback(email_id, result)
            except Exception as e:
                self._logger.error(f"回调函数执行失败: {str(e)}", exc_info=True)

        # 推送检测结果更新事件
        if self._event_service and user_id:
            await self._event_service.publish_detection_update(
                user_id=user_id,
                payload=self._build_event_payload(email_id, result),
            )

        return user_id

    async def _check_whitelist_and_detect(
        self,
        sender: str,
        subject: Optional[str],
        content_text: Optional[str],
        content_html: Optional[str],
        user_id: Optional[int] = None,
    ) -> PhishingResult:
        """检查白名单并决定是否执行检测。

        检测顺序：
        1. 检查发件人是否在白名单中 -> 直接返回正常
        2. 检查所有URL是否都在白名单中 -> 直接返回正常
        3. 否则执行正常检测

        Args:
            sender: 发件人地址。
            subject: 邮件主题。
            content_text: 纯文本内容。
            content_html: HTML内容。
            user_id: 用户ID，用于用户级别的白名单检查。

        Returns:
            钓鱼检测结果。
        """
        # 1. 检查发件人是否在白名单中
        if self._sender_whitelist_matcher:
            try:
                self._logger.info(f"[白名单检查] 开始检查发件人: sender={sender}, user_id={user_id}")
                is_whitelisted = await self._sender_whitelist_matcher.is_sender_whitelisted(sender, user_id)
                self._logger.info(f"[白名单检查] 发件人白名单检查结果: {is_whitelisted}")
                
                if is_whitelisted:
                    self._logger.info(f"发件人 {sender} 在白名单中，跳过检测")
                    return PhishingResult(
                        level=DetectorPhishingLevel.NORMAL,
                        score=0.0,
                        reason="发件人在白名单中，无需检测",
                    )
            except Exception as e:
                self._logger.error(f"检查发件人白名单失败: {str(e)}", exc_info=True)

        # 2. 检查所有URL是否都在白名单中（同时检测HTML超链接和纯文本URL）
        if self._url_whitelist_matcher:
            try:
                # 合并提取：HTML超链接(<a href>) + 纯文本URL
                # 忽略资源链接（图片/CSS/JS等）
                urls = set()
                if content_html:
                    urls.update(
                        UrlWhitelistMatcher.extract_urls_from_html(content_html)
                    )
                if content_text:
                    urls.update(
                        UrlWhitelistMatcher.extract_urls_from_text(content_text)
                    )

                if urls:
                    self._logger.info(f"[白名单检查] 检查URL白名单: urls={list(urls)}, user_id={user_id}")
                    all_whitelisted = (
                        await self._url_whitelist_matcher.check_urls_whitelisted(
                            list(urls), user_id
                        )
                    )
                    self._logger.info(f"[白名单检查] URL白名单检查结果: {all_whitelisted}")
                    
                    if all_whitelisted:
                        self._logger.info(
                            f"邮件中的所有URL ({len(urls)}个) 都在白名单中，跳过检测"
                        )
                        return PhishingResult(
                            level=DetectorPhishingLevel.NORMAL,
                            score=0.0,
                            reason=f"邮件中的所有链接 ({len(urls)}个) 都在白名单中，无需检测",
                        )
            except Exception as e:
                self._logger.error(f"检查URL白名单失败: {str(e)}", exc_info=True)

        # 3. 执行正常检测
        # 根据系统设置动态选择检测器
        if self._system_settings_service:
            enable_rule_based_detection = await self._system_settings_service.is_rule_based_detection_enabled()
            self._logger.info(f"[检测器选择] 规则检测开关: {enable_rule_based_detection}")
            
            if enable_rule_based_detection:
                # 使用混合检测器（BERT + 规则）
                self._logger.info("使用混合检测器（BERT + 规则检测）")
                from app.utils.phishing.hybrid_phishing_detector import HybridPhishingDetector
                from pathlib import Path
                
                model_path = Path("/home/master/my_first_project/Argus/backend/app/utils/phishing/ml_models/bert_phishing_model")
                
                # 更新规则检测器的规则
                if self._rule_based_detector:
                    from app.services.phishing_rule_service import PhishingRuleService
                    from app.crud.phishing_rule_crud import PhishingRuleCrud
                    from app.core.database import DatabaseManager
                    from app.utils.logging.crud_logger import CrudLogger
                    
                    db_manager = DatabaseManager("mysql+aiomysql://argus:argus123@localhost:3306/argus")
                    crud_logger = CrudLogger(self._logger)
                    rule_crud = PhishingRuleCrud(db_manager, crud_logger)
                    rule_service = PhishingRuleService(rule_crud, self._logger)
                    
                    # 获取启用的规则
                    rules = await rule_service.get_active_rules()
                    self._logger.info(f"加载了 {len(rules)} 条启用的规则")
                    
                    # 更新规则检测器
                    self._rule_based_detector.update_rules(rules)
                
                hybrid_detector = HybridPhishingDetector(
                    logger=self._logger,
                    model_path=model_path,
                    enable_rule_based_detection=True,
                    rule_based_detector=self._rule_based_detector
                )
                return await hybrid_detector.detect(
                    subject=subject,
                    sender=sender,
                    content_text=content_text,
                    content_html=content_html,
                )
            else:
                # 使用纯BERT检测器
                self._logger.info("使用纯BERT检测器（规则检测已禁用）")
                return await self._phishing_detector.detect(
                    subject=subject,
                    sender=sender,
                    content_text=content_text,
                    content_html=content_html,
                )
        else:
            # 如果没有系统设置服务，使用默认检测器
            self._logger.info("系统设置服务不可用，使用默认检测器")
            return await self._phishing_detector.detect(
                subject=subject,
                sender=sender,
                content_text=content_text,
                content_html=content_html,
            )

    async def detect_single_email(
        self,
        email_id: int,
    ) -> Optional[Dict[str, Any]]:
        """同步检测单封邮件（用于即时需要结果的场景）。

        检测顺序：
        1. 检查发件人是否在白名单中
        2. 检查所有URL是否都在白名单中
        3. 如果都不在白名单，执行正常检测

        Args:
            email_id: 邮件ID。

        Returns:
            检测结果字典，失败返回None。
        """
        try:
            mailbox_message = await self._email_crud.get_by_id(email_id)
            if not mailbox_message or not mailbox_message.message:
                return None

            message = mailbox_message.message
            body = message.body

            # 使用白名单检测
            result = await self._check_whitelist_and_detect(
                sender=message.sender_address or "",
                subject=message.subject,
                content_text=body.content_text if body else None,
                content_html=body.content_html if body else None,
            )

            # 更新数据库
            phishing_level = self._map_phishing_level(result.level.value)
            await self._email_crud.update_phishing_result(
                message_id=message.id,
                phishing_level=phishing_level,
                phishing_score=result.score,
                phishing_reason=result.reason,
                phishing_status=PhishingStatus.COMPLETED,
            )

            if self._event_service and message.email_account:
                await self._event_service.publish_detection_update(
                    user_id=message.email_account.user_id,
                    payload=self._build_event_payload(email_id, result),
                )

            return {
                "email_id": email_id,
                "phishing_level": result.level.value,
                "phishing_score": result.score,
                "phishing_reason": result.reason,
            }
        except Exception as e:
            self._logger.error(f"检测邮件 {email_id} 失败: {str(e)}", exc_info=True)
            return None

    async def _notify_batch_completed(self, user_ids: Set[int], count: int) -> None:
        """发送批量检测完成事件。

        Args:
            user_ids: 用户ID集合。
            count: 本次检测邮件数量。
        """
        if not self._event_service:
            return

        for user_id in user_ids:
            await self._event_service.publish_batch_completed(
                user_id=user_id,
                payload={"total": count},
            )

    @staticmethod
    def _build_event_payload(email_id: int, result) -> Dict[str, Any]:
        """构建SSE事件数据。

        Args:
            email_id: 邮件ID（mailbox_messages表ID）。
            result: 钓鱼检测结果。

        Returns:
            事件数据字典。
        """
        return {
            "email_id": email_id,
            "phishing_level": result.level.value,
            "phishing_score": result.score,
            "phishing_status": PhishingStatus.COMPLETED.value,
            "phishing_reason": result.reason,
        }

    @staticmethod
    def _map_phishing_level(level: str) -> PhishingLevel:
        """映射钓鱼检测等级到数据库枚举。"""
        level_map = {
            "NORMAL": PhishingLevel.NORMAL,
            "SUSPICIOUS": PhishingLevel.SUSPICIOUS,
            "HIGH_RISK": PhishingLevel.HIGH_RISK,
        }
        return level_map.get(level, PhishingLevel.NORMAL)