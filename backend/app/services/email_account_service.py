"""邮箱账户服务层。"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.crud.email_account_crud import EmailAccountCrud
from app.crud.email_sync_crud import EmailSyncCrud
from app.crud.mailbox_crud import MailboxCrud
from app.entities.email_entity import PhishingLevel, PhishingStatus
from app.schemas.email_account_schema import (
    AddEmailAccountRequest,
    AddEmailAccountResponse,
    EmailAccountListResponse,
    EmailAccountItem,
    SyncEmailsResponse,
    DeleteEmailAccountResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.utils.imap import ImapClient, ImapConfigFactory, SmtpClient
from app.utils.imap.email_parser import EmailParser
from app.utils.imap.imap_models import MailboxInfo
from app.utils.imap.providers import ProviderFactory
from app.utils.phishing import PhishingDetectorInterface


class EmailAccountService:
    """邮箱账户服务类。

    负责邮箱账户的添加、同步、测试连接等业务逻辑。
    """

    def __init__(
        self,
        email_account_crud: EmailAccountCrud,
        mailbox_crud: MailboxCrud,
        email_sync_crud: EmailSyncCrud,
        phishing_detector: PhishingDetectorInterface,
        phishing_detection_service,  # 避免循环导入，使用类型提示的字符串形式
        logger: logging.Logger,
    ) -> None:
        """初始化邮箱账户服务。

        Args:
            email_account_crud: 邮箱账户数据访问对象。
            mailbox_crud: 邮箱文件夹数据访问对象。
            email_sync_crud: 邮件同步写入对象。
            phishing_detector: 钓鱼检测器。
            phishing_detection_service: 钓鱼检测服务（后台异步检测）。
            logger: 日志记录器。
        """
        self._email_account_crud = email_account_crud
        self._mailbox_crud = mailbox_crud
        self._email_sync_crud = email_sync_crud
        self._phishing_detector = phishing_detector
        self._phishing_detection_service = phishing_detection_service
        self._logger = logger
        self._email_parser = EmailParser(logger)

    async def add_email_account(
        self, user_id: int, request: AddEmailAccountRequest
    ) -> AddEmailAccountResponse:
        """添加邮箱账户。

        Args:
            user_id: 用户ID。
            request: 添加邮箱请求。

        Returns:
            添加邮箱响应。
        """
        imap_error = self._ensure_imap_available()
        if imap_error:
            return AddEmailAccountResponse(success=False, message=imap_error)

        smtp_error = self._ensure_smtp_available()
        if smtp_error:
            return AddEmailAccountResponse(success=False, message=smtp_error)

        existing = await self._email_account_crud.get_by_email_address(
            user_id, request.email_address
        )
        if existing:
            return AddEmailAccountResponse(
                success=False,
                message="该邮箱已添加过。",
            )

        try:
            config = ImapConfigFactory.get_config_or_default(
                email_type=request.email_type,
                imap_host=request.imap_host,
                imap_port=request.imap_port,
                smtp_host=request.smtp_host,
                smtp_port=request.smtp_port,
                use_ssl=request.use_ssl,
            )
        except ValueError as exc:
            return AddEmailAccountResponse(
                success=False,
                message=str(exc),
            )

        # 获取对应的邮箱服务商提供者
        provider = ProviderFactory.get_provider(
            request.email_type,
            logger=self._logger,
        )

        # 尝试IMAP连接验证
        try:
            imap_client = ImapClient(config, self._logger, provider=provider)
            connected = await imap_client.connect(
                request.email_address, request.auth_password
            )
            await imap_client.disconnect()

            if not connected:
                self._logger.warning("IMAP连接失败，但继续创建邮箱账户: %s", request.email_address)
        except Exception as e:
            self._logger.warning("IMAP连接验证失败，但继续创建邮箱账户: %s, 错误: %s", request.email_address, str(e))

        # 尝试SMTP连接验证
        try:
            smtp_client = SmtpClient(config, self._logger)
            smtp_connected = await smtp_client.test_connection(
                request.email_address, request.auth_password
            )
            if not smtp_connected:
                self._logger.warning("SMTP连接失败，但继续创建邮箱账户: %s", request.email_address)
        except Exception as e:
            self._logger.warning("SMTP连接验证失败，但继续创建邮箱账户: %s, 错误: %s", request.email_address, str(e))

        account = await self._email_account_crud.create(
            user_id=user_id,
            email_address=request.email_address,
            email_type=request.email_type,
            auth_password=request.auth_password,
            imap_host=config.imap_host,
            imap_port=config.imap_port,
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            use_ssl=config.use_ssl,
        )

        self._logger.info(
            "添加邮箱成功: user_id=%s, email=%s", user_id, request.email_address
        )

        return AddEmailAccountResponse(
            success=True,
            message="邮箱添加成功。",
            account_id=account.id,
            email_address=account.email_address,
        )

    async def get_email_accounts(self, user_id: int) -> EmailAccountListResponse:
        """获取用户的邮箱账户列表。

        Args:
            user_id: 用户ID。

        Returns:
            邮箱账户列表响应。
        """
        accounts = await self._email_account_crud.get_by_user_id(user_id)

        items = [
            EmailAccountItem(
                id=account.id,
                email_address=account.email_address,
                email_type=account.email_type.value,
                is_active=account.is_active,
                last_sync_at=(
                    account.last_sync_at.isoformat() if account.last_sync_at else None
                ),
            )
            for account in accounts
        ]

        return EmailAccountListResponse(success=True, accounts=items)

    async def sync_all_emails(self, user_id: int) -> Dict[str, Any]:
        """同步用户所有邮箱账户的邮件。

        Args:
            user_id: 用户ID。

        Returns:
            同步结果摘要。
        """
        accounts = await self._email_account_crud.get_by_user_id(user_id)
        
        if not accounts:
            return {
                "success": True,
                "total_synced": 0,
                "accounts": [],
                "message": "没有邮箱账户"
            }
        
        total_synced = 0
        results = []
        
        for account in accounts:
            try:
                result = await self.sync_emails(user_id, account.id)
                total_synced += result.synced_count
                results.append({
                    "account_id": account.id,
                    "email": account.email_address,
                    "synced_count": result.synced_count,
                    "success": True
                })
            except Exception as e:
                self._logger.error(f"同步账户 {account.email_address} 失败: {e}")
                results.append({
                    "account_id": account.id,
                    "email": account.email_address,
                    "synced_count": 0,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total_synced": total_synced,
            "accounts": results,
            "message": f"同步完成，共获取 {total_synced} 封新邮件"
        }

    async def sync_emails(self, user_id: int, account_id: int) -> SyncEmailsResponse:
        """同步邮箱邮件。

        Args:
            user_id: 用户ID。
            account_id: 邮箱账户ID。

        Returns:
            同步邮件响应。
        """
        imap_error = self._ensure_imap_available()
        if imap_error:
            self._logger.error("[同步邮件] IMAP不可用: %s", imap_error)
            return SyncEmailsResponse(success=False, message=imap_error)

        account = await self._email_account_crud.get_by_id(account_id)
        if not account or account.user_id != user_id:
            self._logger.error("[同步邮件] 邮箱账户不存在或用户不匹配: account_id=%s, user_id=%s", account_id, user_id)
            return SyncEmailsResponse(
                success=False,
                message="邮箱账户不存在。",
            )

        # 解密密码，添加错误处理
        try:
            password = self._email_account_crud.decrypt_password(
                account.auth_password_encrypted
            )
            if not password:
                self._logger.error("[同步邮件] 密码解密为空: account_id=%s", account_id)
                return SyncEmailsResponse(
                    success=False,
                    message="邮箱密码配置错误，请重新设置。",
                )
        except Exception as decrypt_error:
            self._logger.error("[同步邮件] 密码解密失败: account_id=%s, error=%s", account_id, str(decrypt_error))
            return SyncEmailsResponse(
                success=False,
                message="邮箱密码解密失败，请重新添加邮箱账户。",
            )

        config = ImapConfigFactory.get_config_or_default(
            email_type=account.email_type,
            imap_host=account.imap_host,
            imap_port=account.imap_port,
            smtp_host=account.smtp_host,
            smtp_port=account.smtp_port,
            use_ssl=account.use_ssl,
        )

        # 获取对应的邮箱服务商提供者
        provider = ProviderFactory.get_provider(
            account.email_type,
            logger=self._logger,
        )

        imap_client = ImapClient(config, self._logger, provider=provider)
        
        # 连接邮箱，添加详细的错误处理
        try:
            connected = await imap_client.connect(account.email_address, password)
        except Exception as connect_error:
            self._logger.error("[同步邮件] 连接邮箱失败: account_id=%s, email=%s, error=%s", 
                             account_id, account.email_address, str(connect_error))
            return SyncEmailsResponse(
                success=False,
                message=f"连接邮箱失败: {str(connect_error)}",
            )

        if not connected:
            self._logger.error("[同步邮件] 邮箱连接失败: account_id=%s, email=%s", 
                             account_id, account.email_address)
            return SyncEmailsResponse(
                success=False,
                message="邮箱连接失败，请检查邮箱配置和网络连接。",
            )

        synced_total = 0
        # 首次同步：获取所有邮件（不限制数量）
        initial_sync_limit = None
        remaining_quota = None
        is_initial_sync = False  # 是否为首次同步

        try:
            mailboxes = await imap_client.list_mailboxes()
            if not mailboxes:
                mailboxes = [MailboxInfo(name="INBOX", delimiter=None, attributes=None)]
        except Exception as list_error:
            self._logger.error("[同步邮件] 获取邮箱文件夹列表失败: account_id=%s, error=%s", 
                             account_id, str(list_error))
            return SyncEmailsResponse(
                success=False,
                message=f"获取邮箱文件夹失败: {str(list_error)}",
            )

        try:
            # 检查是否为首次同步（任意文件夹的last_uid为0即为首次同步）
            for mailbox in mailboxes:
                if mailbox.attributes and "\\NOSELECT" in mailbox.attributes.upper():
                    continue
                try:
                    mailbox_entity_check = await self._mailbox_crud.get_by_account_and_name(
                        account_id, mailbox.name
                    )
                except Exception as check_error:
                    self._logger.warning("[同步邮件] 检查邮箱文件夹失败: account_id=%s, mailbox=%s, error=%s",
                                       account_id, mailbox.name, str(check_error))
                    mailbox_entity_check = None
                    
                if (
                    not mailbox_entity_check
                    or (mailbox_entity_check.last_uid or 0) == 0
                ):
                    is_initial_sync = True
                    break

            for mailbox in mailboxes:
                if mailbox.attributes and "\\NOSELECT" in mailbox.attributes.upper():
                    continue

                try:
                    status = await imap_client.get_mailbox_status(mailbox.name)
                except Exception as status_error:
                    self._logger.warning("[同步邮件] 获取邮箱文件夹状态失败: account_id=%s, mailbox=%s, error=%s",
                                       account_id, mailbox.name, str(status_error))
                    continue

                try:
                    mailbox_entity, uid_changed = await self._mailbox_crud.upsert_mailbox(
                        account_id=account_id,
                        name=mailbox.name,
                        delimiter=mailbox.delimiter,
                        attributes=mailbox.attributes,
                        uid_validity=status.uid_validity,
                    )
                except Exception as upsert_error:
                    self._logger.error("[同步邮件] 更新邮箱文件夹失败: account_id=%s, mailbox=%s, error=%s",
                                     account_id, mailbox.name, str(upsert_error))
                    continue

                if uid_changed:
                    # UIDVALIDITY变化意味着UID游标失效，需清空文件夹映射后重新同步。
                    try:
                        await self._mailbox_crud.reset_mailbox_messages(mailbox_entity.id)
                    except Exception as reset_error:
                        self._logger.error("[同步邮件] 重置邮箱文件夹邮件失败: account_id=%s, mailbox=%s, error=%s",
                                         account_id, mailbox.name, str(reset_error))
                        continue

                selected = await imap_client.select_mailbox(mailbox.name)
                if not selected:
                    self._logger.warning("无法选择文件夹，跳过: %s", mailbox.name)
                    continue

                last_uid = mailbox_entity.last_uid or 0
                
                # 首次同步：获取所有邮件（从UID 1开始）
                if last_uid == 0:
                    self._logger.info("[同步邮件] 首次同步，获取所有邮件，start_uid=1")
                    try:
                        uids = await imap_client.fetch_uids_since(1)
                        if uids:
                            uids = sorted(uids)
                            self._logger.info("[同步邮件] 首次同步找到 %d 封邮件", len(uids))
                    except Exception as fetch_error:
                        self._logger.error("[同步邮件] 获取邮件UID列表失败: account_id=%s, mailbox=%s, error=%s",
                                         account_id, mailbox.name, str(fetch_error))
                        continue
                else:
                    # 非首次同步：增量获取新邮件
                    start_uid = last_uid + 1
                    self._logger.info("[同步邮件] 增量同步，start_uid=%d", start_uid)
                    try:
                        uids = await imap_client.fetch_uids_since(start_uid)
                        if uids:
                            uids = sorted(uids)
                            self._logger.info("[同步邮件] 增量同步找到 %d 封新邮件", len(uids))
                    except Exception as fetch_error:
                        self._logger.error("[同步邮件] 获取新邮件UID列表失败: account_id=%s, mailbox=%s, error=%s",
                                         account_id, mailbox.name, str(fetch_error))
                        continue

                if not uids:
                    try:
                        await self._mailbox_crud.update_sync_state(
                            mailbox_entity.id, last_uid
                        )
                    except Exception as update_error:
                        self._logger.warning("[同步邮件] 更新同步状态失败: account_id=%s, mailbox=%s, error=%s",
                                           account_id, mailbox.name, str(update_error))
                    continue

                # 收集所有新邮件的ID，用于后台异步检测
                new_email_ids = []

                for chunk in self._chunk_list(uids, 50):
                    # 分批拉取邮件与批量写入，避免单次内存占用过高。
                    self._logger.info("[同步邮件] 处理批次: 当前批次=%d 封邮件", len(chunk))
                    
                    try:
                        fetched_emails = await imap_client.fetch_emails_by_uid(chunk)
                    except Exception as fetch_error:
                        self._logger.error("[同步邮件] 批次获取邮件失败: account_id=%s, mailbox=%s, chunk_size=%d, error=%s",
                                         account_id, mailbox.name, len(chunk), str(fetch_error))
                        continue
                    
                    try:
                        payloads = self._build_payloads(fetched_emails, mailbox.name)
                    except Exception as build_error:
                        self._logger.error("[同步邮件] 构建邮件payloads失败: account_id=%s, mailbox=%s, error=%s",
                                         account_id, mailbox.name, str(build_error))
                        continue
                        
                    if not payloads:
                        self._logger.warning("[同步邮件] 批次处理失败: 没有生成payloads")
                        continue

                    # 先保存邮件，不进行检测（默认为NORMAL），避免阻塞用户
                    # 钓鱼检测将在后台异步执行
                    for payload in payloads:
                        payload["phishing_level"] = PhishingLevel.NORMAL
                        payload["phishing_score"] = 0.0
                        payload["phishing_reason"] = None
                        payload["phishing_status"] = PhishingStatus.COMPLETED.value  # 直接设置为已完成

                    try:
                        synced_count, batch_email_ids = await self._email_sync_crud.save_mailbox_emails(
                            account_id=account_id,
                            mailbox_id=mailbox_entity.id,
                            payloads=payloads,
                        )
                    except Exception as save_error:
                        self._logger.error("[同步邮件] 批次保存邮件失败: account_id=%s, mailbox=%s, error=%s",
                                         account_id, mailbox.name, str(save_error))
                        continue

                    synced_total += synced_count
                    self._logger.info("[同步邮件] 批次完成: 保存=%d 封, 累计=%d 封", 
                                   synced_count, synced_total)

                    # 收集新邮件ID用于后台检测
                    new_email_ids.extend(batch_email_ids)

                    try:
                        await self._mailbox_crud.update_sync_state(
                            mailbox_entity.id, max(chunk)
                        )
                    except Exception as update_error:
                        self._logger.warning("[同步邮件] 更新同步状态失败: account_id=%s, mailbox=%s, error=%s",
                                           account_id, mailbox.name, str(update_error))

                # 启动后台异步检测任务（不等待完成）
                if new_email_ids:
                    self._logger.info(
                        "启动后台钓鱼检测任务: account_id=%d, mailbox=%s, count=%d",
                        account_id,
                        mailbox.name,
                        len(new_email_ids),
                    )
                    # 异步检测邮件，不阻塞主流程
                    try:
                        await self._phishing_detection_service.detect_emails_async(
                            new_email_ids
                        )
                    except Exception as detect_error:
                        self._logger.error("[同步邮件] 启动钓鱼检测失败: account_id=%s, mailbox=%s, error=%s",
                                         account_id, mailbox.name, str(detect_error))

            await self._email_account_crud.update_last_sync(account_id)

            return SyncEmailsResponse(
                success=True,
                message=f"同步成功，获取{synced_total}封新邮件。",
                synced_count=synced_total,
            )
        except Exception as sync_error:
            self._logger.error("[同步邮件] 同步过程中发生未预期错误: account_id=%s, error=%s", 
                             account_id, str(sync_error))
            return SyncEmailsResponse(
                success=False,
                message=f"同步失败: {str(sync_error)}",
            )
        finally:
            await imap_client.disconnect()

    async def delete_email_account(
        self, user_id: int, account_id: int
    ) -> DeleteEmailAccountResponse:
        """删除邮箱账户。

        Args:
            user_id: 用户ID。
            account_id: 邮箱账户ID。

        Returns:
            删除邮箱响应。
        """
        account = await self._email_account_crud.get_by_id(account_id)
        if not account or account.user_id != user_id:
            return DeleteEmailAccountResponse(
                success=False,
                message="邮箱账户不存在。",
            )

        await self._email_account_crud.delete(account_id)

        self._logger.info("删除邮箱成功: account_id=%s", account_id)

        return DeleteEmailAccountResponse(
            success=True,
            message="邮箱删除成功。",
        )

    async def reset_sync_state(self, user_id: int, account_id: int) -> None:
        """重置邮箱账户的同步状态，确保下次同步所有邮件。

        Args:
            user_id: 用户ID。
            account_id: 邮箱账户ID。
        """
        # 验证账户所有权
        account = await self._email_account_crud.get_by_id(account_id)
        if not account or account.user_id != user_id:
            raise ValueError("邮箱账户不存在或无权限")

        # 获取所有邮箱文件夹
        mailboxes = await self._mailbox_crud.get_by_account_id(account_id)
        
        # 重置每个文件夹的 last_uid 为 0
        for mailbox in mailboxes:
            await self._mailbox_crud.update_sync_state(mailbox.id, 0)
            self._logger.info("[重置同步状态] 文件夹 %s 的 last_uid 已重置为 0", mailbox.name)
        
        self._logger.info("[重置同步状态] 邮箱账户 %d 的同步状态已重置，共重置 %d 个文件夹", 
                        account_id, len(mailboxes))

    async def test_connection(
        self, request: TestConnectionRequest
    ) -> TestConnectionResponse:
        """测试邮箱连接。

        Args:
            request: 测试连接请求。

        Returns:
            测试连接响应。
        """
        imap_error = self._ensure_imap_available()
        if imap_error:
            return TestConnectionResponse(success=False, message=imap_error)

        try:
            config = ImapConfigFactory.get_config_or_default(
                email_type=request.email_type,
                imap_host=request.imap_host,
                imap_port=request.imap_port,
                use_ssl=request.use_ssl,
            )
        except ValueError as exc:
            return TestConnectionResponse(
                success=False,
                message=str(exc),
            )

        # 获取对应的邮箱服务商提供者
        provider = ProviderFactory.get_provider(
            request.email_type,
            logger=self._logger,
        )

        imap_client = ImapClient(config, self._logger, provider=provider)
        connected = await imap_client.connect(
            request.email_address, request.auth_password
        )
        await imap_client.disconnect()

        if connected:
            return TestConnectionResponse(
                success=True,
                message="连接成功。",
            )
        return TestConnectionResponse(
            success=False,
            message="连接失败，请检查邮箱地址和授权密码。",
        )

    def _build_payloads(self, fetched_emails, mailbox_name: str) -> List[dict]:
        """构建同步写入的数据载荷。"""
        payloads: List[dict] = []
        parsed_count = 0
        failed_count = 0
        
        for fetched in fetched_emails:
            try:
                parsed = self._email_parser.parse(fetched.raw_bytes)
                if not parsed:
                    failed_count += 1
                    self._logger.warning("[构建payloads] 邮件解析失败: UID=%d, 大小=%d 字节", 
                                      fetched.uid, fetched.size)
                    continue
                
                parsed_count += 1
                message_id = parsed.message_id or self._fallback_message_id(
                    mailbox_name, fetched.uid
                )
                payloads.append(
                    {
                        "uid": fetched.uid,
                        "flags": fetched.flags,
                        "internal_date": fetched.internal_date,
                        "size": fetched.size,
                        "message_id": message_id,
                        "subject": parsed.subject,
                        "sender_name": parsed.sender_name,
                        "sender_address": parsed.sender_address,
                        "recipients": parsed.recipients,
                        "content_text": parsed.content_text,
                        "content_html": parsed.content_html,
                        "snippet": parsed.snippet,
                        "received_at": parsed.received_at or fetched.internal_date,
                    }
                )
            except Exception as e:
                failed_count += 1
                self._logger.error("[构建payloads] 处理邮件异常: UID=%d, 错误=%s", 
                                 fetched.uid, str(e))
        
        self._logger.info("[构建payloads] 完成: 解析成功=%d, 解析失败=%d, 生成payloads=%d", 
                        parsed_count, failed_count, len(payloads))
        return payloads

    def _fallback_message_id(self, mailbox_name: str, uid: int) -> str:
        """生成缺失Message-ID时的替代值。"""
        message_id = f"missing-{mailbox_name}-{uid}"
        return message_id[:255]

    def _chunk_list(self, values: List[int], chunk_size: int) -> List[List[int]]:
        """将列表按指定大小切分为子列表。"""
        return [values[i : i + chunk_size] for i in range(0, len(values), chunk_size)]

    def _map_phishing_level(self, level: str) -> PhishingLevel:
        """映射钓鱼检测等级到数据库枚举。"""
        level_map = {
            "NORMAL": PhishingLevel.NORMAL,
            "SUSPICIOUS": PhishingLevel.SUSPICIOUS,
            "HIGH_RISK": PhishingLevel.HIGH_RISK,
        }
        return level_map.get(level, PhishingLevel.NORMAL)

    def _ensure_imap_available(self) -> Optional[str]:
        """确保IMAP依赖可用。"""
        if ImapClient is None:
            return "IMAP依赖未安装，请先安装aioimaplib。"
        return None

    def _ensure_smtp_available(self) -> Optional[str]:
        """确保SMTP依赖可用。"""
        if SmtpClient is None:
            return "SMTP依赖未安装，请先安装aiosmtplib。"
        return None