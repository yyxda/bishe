"""异步SMTP客户端模块。

基于aiosmtplib封装的异步SMTP邮件发送客户端。
"""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

import aiosmtplib

from app.utils.imap.imap_config import ImapConfig


class SmtpClient:
    """异步SMTP客户端类。

    提供邮件发送功能。
    """

    def __init__(self, config: ImapConfig, logger: Optional[logging.Logger] = None):
        """初始化SMTP客户端。

        Args:
            config: IMAP/SMTP配置。
            logger: 日志记录器。
        """
        self._config = config
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    async def send_email(
        self,
        username: str,
        password: str,
        to_addresses: List[str],
        subject: str,
        content: str,
        content_html: Optional[str] = None,
        cc_addresses: Optional[List[str]] = None,
    ) -> bool:
        """发送邮件。

        Args:
            username: 发件人邮箱地址。
            password: 授权密码。
            to_addresses: 收件人列表。
            subject: 邮件主题。
            content: 纯文本内容。
            content_html: HTML内容（可选）。
            cc_addresses: 抄送人列表（可选）。

        Returns:
            是否发送成功。
        """
        try:
            # 创建邮件
            if content_html:
                msg = MIMEMultipart("alternative")
                msg.attach(MIMEText(content, "plain", "utf-8"))
                msg.attach(MIMEText(content_html, "html", "utf-8"))
            else:
                msg = MIMEText(content, "plain", "utf-8")

            msg["Subject"] = subject
            msg["From"] = username
            msg["To"] = ", ".join(to_addresses)
            if cc_addresses:
                msg["Cc"] = ", ".join(cc_addresses)

            # 发送邮件
            all_recipients = to_addresses + (cc_addresses or [])

            await aiosmtplib.send(
                msg,
                hostname=self._config.smtp_host,
                port=self._config.smtp_port,
                username=username,
                password=password,
                use_tls=self._config.use_ssl,
            )

            self._logger.info("邮件发送成功: to=%s", to_addresses)
            return True

        except Exception as e:
            self._logger.error("邮件发送失败: %s", e)
            return False

    async def test_connection(self, username: str, password: str) -> bool:
        """测试SMTP连接。

        Args:
            username: 邮箱地址。
            password: 授权密码。

        Returns:
            是否连接成功。
        """
        smtp = None
        try:
            smtp = aiosmtplib.SMTP(
                hostname=self._config.smtp_host,
                port=self._config.smtp_port,
                use_tls=self._config.use_ssl,
                timeout=10,
            )
            await smtp.connect()
            if not self._config.use_ssl:
                try:
                    await smtp.starttls()
                except Exception as exc:
                    self._logger.warning("SMTP STARTTLS失败: %s", exc)

            await smtp.login(username, password)
            await smtp.quit()

            self._logger.info("SMTP连接成功: %s", username)
            return True
        except Exception as exc:
            self._logger.error("SMTP连接失败: %s", exc)
            if smtp:
                try:
                    await smtp.quit()
                except Exception:
                    pass
            return False
