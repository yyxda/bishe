"""URL白名单匹配服务。

提供URL域名规则匹配功能，支持Clash风格的域名规则。
"""

import logging
import re
from typing import List, Optional
from urllib.parse import urlparse

from app.crud.url_whitelist_crud import UrlWhitelistCrud
from app.entities.url_whitelist_entity import UrlWhitelistEntity


class UrlWhitelistMatcher:
    """URL白名单匹配器。

    支持三种Clash风格的域名匹配规则：
    - DOMAIN: 精确匹配域名
    - DOMAIN-SUFFIX: 匹配域名后缀
    - DOMAIN-KEYWORD: 匹配域名中的关键词
    """

    # 规则类型常量
    RULE_DOMAIN = "DOMAIN"
    RULE_DOMAIN_SUFFIX = "DOMAIN-SUFFIX"
    RULE_DOMAIN_KEYWORD = "DOMAIN-KEYWORD"

    # 资源扩展名黑名单（不检测这些链接，通常是图片/CSS/JS等资源）
    RESOURCE_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".ico",
        ".bmp",
        ".css",
        ".js",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".otf",
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
    }

    def __init__(
        self,
        whitelist_crud: UrlWhitelistCrud,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """初始化URL白名单匹配器。

        Args:
            whitelist_crud: 白名单CRUD实例。
            logger: 日志记录器。
        """
        self._whitelist_crud = whitelist_crud
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._cached_rules: Optional[List[UrlWhitelistEntity]] = None

    async def refresh_rules(self, user_id: Optional[int] = None) -> None:
        """刷新规则缓存。

        Args:
            user_id: 用户ID，如果为None则获取所有启用的规则（包括全局和用户规则）。
        """
        self._cached_rules = await self._whitelist_crud.get_all_active(user_id)
        self._logger.info(f"刷新白名单规则缓存，共 {len(self._cached_rules)} 条规则")

    async def is_url_whitelisted(self, url: str, user_id: Optional[int] = None) -> bool:
        """检查URL是否在白名单中。

        Args:
            url: 要检查的URL。
            user_id: 用户ID，用于用户级别的白名单检查。

        Returns:
            如果URL在白名单中返回True，否则返回False。
        """
        domain = self.extract_domain(url)
        if not domain:
            return False

        # 每次检查时都刷新规则缓存，确保获取最新规则
        # 获取全局白名单和该用户的白名单
        await self.refresh_rules(user_id)

        rules = self._cached_rules or []
        
        self._logger.debug(f"[URL白名单] 检查URL: {url}, user_id: {user_id}, 规则数量: {len(rules)}")

        for rule in rules:
            if self._match_rule(domain, rule.rule_type, rule.rule_value):
                self._logger.debug(
                    f"URL '{url}' 匹配白名单规则: {rule.rule_type}:{rule.rule_value}"
                )
                return True

        return False

    async def check_urls_whitelisted(self, urls: List[str], user_id: Optional[int] = None) -> bool:
        """检查URL列表是否全部在白名单中。

        Args:
            urls: URL列表。
            user_id: 用户ID，用于用户级别的白名单检查。

        Returns:
            如果所有URL都在白名单中返回True，否则返回False。
        """
        if not urls:
            return False

        for url in urls:
            if not await self.is_url_whitelisted(url, user_id):
                return False

        return True

    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """从URL中提取域名部分。

        仅提取域名，不包含路径、查询参数等。

        Args:
            url: 完整的URL字符串。

        Returns:
            域名字符串，如果解析失败返回None。
        """
        try:
            # 如果没有协议前缀，添加http://以便解析
            if not url.startswith(("http://", "https://")):
                url = "http://" + url

            parsed = urlparse(url)
            hostname = parsed.hostname

            if hostname:
                # 移除端口号（如果有）
                return hostname.lower()

            return None
        except Exception:
            return None

    def _match_rule(self, domain: str, rule_type: str, rule_value: str) -> bool:
        """检查域名是否匹配规则。

        Args:
            domain: 要检查的域名。
            rule_type: 规则类型。
            rule_value: 规则值。

        Returns:
            是否匹配。
        """
        domain = domain.lower()
        rule_value = rule_value.lower()

        if rule_type == self.RULE_DOMAIN:
            # 精确匹配
            return domain == rule_value

        elif rule_type == self.RULE_DOMAIN_SUFFIX:
            # 后缀匹配
            # 例如: mail.qq.com 匹配 qq.com
            # 但 notqq.com 不应匹配 qq.com
            if domain == rule_value:
                return True
            if domain.endswith("." + rule_value):
                return True
            return False

        elif rule_type == self.RULE_DOMAIN_KEYWORD:
            # 关键词匹配
            return rule_value in domain

        return False

    @classmethod
    def is_resource_url(cls, url: str) -> bool:
        """判断URL是否为资源链接（图片/CSS/JS等）。

        这类链接不会被用户直接点击，不构成钓鱼风险。

        Args:
            url: URL字符串。

        Returns:
            如果是资源链接返回True，否则返回False。
        """
        # 移除查询参数后检查扩展名
        path = url.split("?")[0].lower()
        return any(path.endswith(ext) for ext in cls.RESOURCE_EXTENSIONS)

    @classmethod
    def extract_urls_from_html(cls, html_content: str) -> List[str]:
        """从HTML内容中提取用户可点击的超链接。

        只提取 <a href="..."> 中的URL，忽略 <img src>, <link href>,
        <script src> 等资源引用链接，这些不会被用户直接点击。

        Args:
            html_content: HTML内容。

        Returns:
            用户可点击的URL列表（已去重和过滤资源链接）。
        """
        if not html_content:
            return []

        # 只匹配 <a 标签中的 href 属性
        pattern = r'<a\s+[^>]*href\s*=\s*["\']?(https?://[^"\'>\s]+)'
        urls = re.findall(pattern, html_content, re.IGNORECASE)

        # 去重并过滤资源链接
        return [url for url in set(urls) if not cls.is_resource_url(url)]

    @classmethod
    def extract_urls_from_text(cls, text_content: str) -> List[str]:
        """从纯文本内容中提取URL。

        用于检测钓鱼邮件中直接展示URL文本的情况，
        例如："请复制以下链接 http://evil.xyz/..."

        Args:
            text_content: 纯文本内容。

        Returns:
            URL列表（已去重和过滤资源链接）。
        """
        if not text_content:
            return []

        # 匹配http/https开头的URL
        pattern = r'https?://[^\s<>"\'()\[\]{}]+'
        urls = re.findall(pattern, text_content, re.IGNORECASE)

        # 去重并过滤资源链接
        return [url for url in set(urls) if not cls.is_resource_url(url)]