"""长URL检测器模块。

检测邮件中的长URL，包括纯文本URL和HTML超链接中的实际URL。
"""

import re
import logging
from typing import Any, Dict, List, Optional
from html.parser import HTMLParser

from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingResult,
    PhishingLevel,
)
from app.utils.phishing.score_level_mapper import ScoreLevelMapper


class LinkExtractor(HTMLParser):
    """HTML链接提取器。

    用于从HTML内容中提取所有超链接的实际URL。
    """

    def __init__(self):
        super().__init__()
        self.links = []
        self.link_texts = []

    def handle_starttag(self, tag: str, attrs: list):
        """处理HTML开始标签。"""
        if tag.lower() == 'a':
            for attr_name, attr_value in attrs:
                if attr_name.lower() == 'href' and attr_value:
                    self.links.append(attr_value)

    def handle_data(self, data: str):
        """处理标签内的文本数据。"""
        if self.lasttag and self.lasttag.lower() == 'a':
            self.link_texts.append(data.strip())


class LongUrlDetector(PhishingDetectorInterface):
    """长URL检测器。

    检测邮件中的长URL，当URL超过指定长度时判定为高危钓鱼邮件。
    同时检测HTML中的超链接伪装（显示文本与实际URL不符）。
    """

    # URL长度阈值（字符数）
    URL_LENGTH_THRESHOLD = 150

    # 可疑URL长度（触发疑似钓鱼）
    SUSPICIOUS_URL_LENGTH = 100

    # 超链接伪装检测：显示文本与实际URL差异过大
    LINK_DISGUISE_THRESHOLD = 0.3  # 相似度低于此值视为伪装

    def __init__(
        self,
        url_length_threshold: int = URL_LENGTH_THRESHOLD,
        suspicious_url_length: int = SUSPICIOUS_URL_LENGTH,
        logger: Optional[logging.Logger] = None,
        score_mapper: Optional[ScoreLevelMapper] = None,
    ):
        """初始化长URL检测器。

        Args:
            url_length_threshold: URL长度阈值，超过此长度判定为高危。
            suspicious_url_length: 可疑URL长度，超过此长度判定为疑似。
            logger: 日志记录器。
            score_mapper: 置信度映射器。
        """
        self._url_length_threshold = url_length_threshold
        self._suspicious_url_length = suspicious_url_length
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._score_mapper = score_mapper or ScoreLevelMapper()

    async def detect(
        self,
        subject: Optional[str],
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
        headers: Optional[Dict[str, str]] = None,
    ) -> PhishingResult:
        """检测邮件中的长URL。

        Args:
            subject: 邮件主题。
            sender: 发件人。
            content_text: 纯文本内容。
            content_html: HTML内容。
            headers: 邮件头信息（可选）。

        Returns:
            钓鱼检测结果。
        """
        score = 0.0
        reasons = []

        # 1. 检测纯文本中的URL
        text_urls = self._extract_text_urls(content_text)
        long_text_urls = [url for url in text_urls if len(url) > self._url_length_threshold]
        suspicious_text_urls = [
            url for url in text_urls
            if self._suspicious_url_length < len(url) <= self._url_length_threshold
        ]

        if long_text_urls:
            score = 1.0  # 直接判定为高危
            reasons.append(f"检测到{len(long_text_urls)}个超长URL(长度>{self._url_length_threshold})")
            for url in long_text_urls[:3]:  # 最多显示3个示例
                reasons.append(f"  - URL长度: {len(url)}字符")

        # 2. 检测HTML中的超链接
        if content_html:
            html_links = self._extract_html_links(content_html)
            long_html_links = [link for link in html_links if len(link) > self._url_length_threshold]
            suspicious_html_links = [
                link for link in html_links
                if self._suspicious_url_length < len(link) <= self._url_length_threshold
            ]

            # 检测超链接伪装（显示文本与实际URL差异大）
            disguised_links = self._detect_link_disguise(content_html)

            if long_html_links:
                score = max(score, 1.0)
                reasons.append(f"检测到{len(long_html_links)}个超长超链接(长度>{self._url_length_threshold})")
                for link in long_html_links[:3]:
                    reasons.append(f"  - 链接长度: {len(link)}字符")

            if disguised_links:
                score = max(score, 0.9)  # 伪装链接也是高危
                reasons.append(f"检测到{len(disguised_links)}个伪装超链接")
                for display_text, actual_url in disguised_links[:3]:
                    reasons.append(f"  - 显示为'{display_text}'，实际指向长URL(长度:{len(actual_url)})")

            if not long_html_links and suspicious_html_links:
                score = max(score, self._score_mapper.suspicious_threshold)
                reasons.append(f"检测到{len(suspicious_html_links)}个可疑长度链接")

        # 3. 如果没有高危，但有可疑URL
        if score < self._score_mapper.high_risk_threshold and suspicious_text_urls:
            score = max(score, self._score_mapper.suspicious_threshold)
            reasons.append(f"检测到{len(suspicious_text_urls)}个可疑长度URL")

        # 确定危险等级
        level = self._score_mapper.get_level(score)

        reason = "; ".join(reasons) if reasons else "未检测到长URL威胁"

        self._logger.debug(
            "长URL检测完成: level=%s, score=%.2f, reason=%s",
            level.value, score, reason
        )

        return PhishingResult(
            level=level,
            score=round(score, 4),
            reason=reason,
        )

    async def batch_detect(
        self,
        emails: List[Dict[str, Any]],
    ) -> List[PhishingResult]:
        """批量检测邮件。

        Args:
            emails: 邮件列表。

        Returns:
            钓鱼检测结果列表。
        """
        results = []
        for email_data in emails:
            result = await self.detect(
                subject=email_data.get("subject"),
                sender=email_data.get("sender", ""),
                content_text=email_data.get("content_text"),
                content_html=email_data.get("content_html"),
                headers=email_data.get("headers"),
            )
            results.append(result)
        return results

    def get_model_info(self) -> Dict[str, Any]:
        """获取检测器信息。

        Returns:
            检测器信息字典。
        """
        return {
            "model_version": "long-url-detector-1.0.0",
            "model_path": None,
            "is_loaded": True,
            "mode": "rule_based_url",
            "url_length_threshold": self._url_length_threshold,
            "suspicious_url_length": self._suspicious_url_length,
        }

    async def reload_model(self) -> bool:
        """热加载模型（规则检测器无需重载）。

        Returns:
            始终返回True。
        """
        self._logger.info("长URL检测器无需重新加载模型")
        return True

    def _extract_text_urls(self, text: Optional[str]) -> List[str]:
        """从纯文本中提取URL。

        Args:
            text: 纯文本内容。

        Returns:
            URL列表。
        """
        if not text:
            return []

        # 匹配http/https开头的URL
        url_pattern = r'https?://[^\s<>"\'\(\)\[\]{}]+'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        return urls

    def _extract_html_links(self, html: str) -> List[str]:
        """从HTML中提取超链接的实际URL。

        Args:
            html: HTML内容。

        Returns:
            URL列表。
        """
        try:
            extractor = LinkExtractor()
            extractor.feed(html)
            # 只返回http/https协议的链接
            return [
                link for link in extractor.links
                if link.startswith(('http://', 'https://'))
            ]
        except Exception as e:
            self._logger.warning("HTML链接提取失败: %s", str(e))
            return []

    def _detect_link_disguise(self, html: str) -> List[tuple]:
        """检测超链接伪装。

        检测显示文本与实际URL差异较大的情况。
        例如：<a href="http://malicious-long-url...">www.baidu.com</a>

        Args:
            html: HTML内容。

        Returns:
            伪装链接列表 [(显示文本, 实际URL), ...]
        """
        try:
            # 提取所有<a>标签及其内容
            link_pattern = r'<a\s+[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>'
            matches = re.findall(link_pattern, html, re.IGNORECASE | re.DOTALL)

            disguised = []
            for actual_url, display_html in matches:
                # 去除display_html中的HTML标签，获取纯文本
                display_text = re.sub(r'<[^>]+>', '', display_html).strip()

                # 如果实际URL很长，但显示文本很短或完全不同，可能是伪装
                if len(actual_url) > self._suspicious_url_length:
                    # 检查显示文本是否是常见的正常域名（如baidu.com等）
                    if display_text and not actual_url.startswith('http://' + display_text) and \
                       not actual_url.startswith('https://' + display_text):
                        # 进一步检查：如果显示文本看起来像域名，但URL很长，可能是伪装
                        if re.match(r'^(www\.)?[\w\-]+\.[a-z]{2,}$', display_text, re.IGNORECASE):
                            disguised.append((display_text, actual_url))

            return disguised
        except Exception as e:
            self._logger.warning("超链接伪装检测失败: %s", str(e))
            return []
