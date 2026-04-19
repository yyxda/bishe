"""钓鱼检测规则引擎模块。

提供基于规则的钓鱼邮件检测功能，支持多种规则类型。
"""

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

from app.entities.phishing_rule_entity import PhishingRuleEntity


class RuleBasedPhishingDetector:
    """基于规则的钓鱼检测器。

    支持多种规则类型：
    - URL规则：检测URL特征
    - SENDER规则：检测发件人特征
    - CONTENT规则：检测邮件内容特征
    - STRUCTURE规则：检测邮件结构特征
    """

    # 规则类型常量
    RULE_TYPE_URL = "URL"
    RULE_TYPE_SENDER = "SENDER"
    RULE_TYPE_CONTENT = "CONTENT"
    RULE_TYPE_STRUCTURE = "STRUCTURE"

    def __init__(
        self,
        rules: List[PhishingRuleEntity],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """初始化规则检测器。

        Args:
            rules: 钓鱼检测规则列表。
            logger: 日志记录器。
        """
        self._rules = rules
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._compile_rules()

    def _compile_rules(self) -> None:
        """编译规则，将正则表达式预编译。"""
        self._compiled_rules: Dict[str, List[Dict]] = {
            self.RULE_TYPE_URL: [],
            self.RULE_TYPE_SENDER: [],
            self.RULE_TYPE_CONTENT: [],
            self.RULE_TYPE_STRUCTURE: [],
        }

        for rule in self._rules:
            if not rule.is_active:
                continue

            try:
                compiled_pattern = re.compile(rule.rule_pattern, re.IGNORECASE | re.UNICODE)
                rule_dict = {
                    "id": rule.id,
                    "name": rule.rule_name,
                    "pattern": compiled_pattern,
                    "original_pattern": rule.rule_pattern,
                    "description": rule.rule_description,
                    "severity": rule.severity,
                }
                self._compiled_rules[rule.rule_type].append(rule_dict)
                self._logger.debug(
                    f"编译规则: {rule.rule_name} ({rule.rule_type}), 严重程度: {rule.severity}"
                )
            except re.error as e:
                self._logger.error(
                    f"规则编译失败: {rule.rule_name}, 模式: {rule.rule_pattern}, 错误: {e}"
                )

    def update_rules(self, rules: List[PhishingRuleEntity]) -> None:
        """更新规则列表。

        Args:
            rules: 新的钓鱼检测规则列表。
        """
        self._rules = rules
        self._compile_rules()
        self._logger.info(f"规则已更新，共 {len(rules)} 条规则")

    def detect(
        self,
        subject: Optional[str],
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
    ) -> Dict[str, any]:
        """使用规则检测邮件是否为钓鱼邮件。

        Args:
            subject: 邮件主题。
            sender: 发件人。
            content_text: 纯文本内容。
            content_html: HTML内容。

        Returns:
            检测结果字典，包含：
            - is_phishing: 是否为钓鱼邮件
            - score: 钓鱼分数（0-1）
            - matched_rules: 匹配的规则列表
            - reasons: 检测原因列表
        """
        matched_rules = []
        total_severity = 0
        max_severity = 0

        # 1. 检测URL规则
        url_matches = self._detect_url_rules(content_text, content_html)
        matched_rules.extend(url_matches)
        for match in url_matches:
            total_severity += match["severity"]
            max_severity = max(max_severity, match["severity"])

        # 2. 检测发件人规则
        sender_matches = self._detect_sender_rules(sender)
        matched_rules.extend(sender_matches)
        for match in sender_matches:
            total_severity += match["severity"]
            max_severity = max(max_severity, match["severity"])

        # 3. 检测内容规则
        content_matches = self._detect_content_rules(subject, content_text)
        matched_rules.extend(content_matches)
        for match in content_matches:
            total_severity += match["severity"]
            max_severity = max(max_severity, match["severity"])

        # 4. 检测结构规则
        structure_matches = self._detect_structure_rules(sender, content_text, content_html)
        matched_rules.extend(structure_matches)
        for match in structure_matches:
            total_severity += match["severity"]
            max_severity = max(max_severity, match["severity"])

        # 计算钓鱼分数
        score = self._calculate_score(matched_rules, max_severity)

        # 生成检测原因
        reasons = [rule["description"] for rule in matched_rules]

        is_phishing = score > 0.5

        self._logger.info(
            f"规则检测完成: 匹配规则数={len(matched_rules)}, "
            f"总分={total_severity}, 最高分={max_severity}, 钓鱼分数={score:.4f}"
        )

        return {
            "is_phishing": is_phishing,
            "score": score,
            "matched_rules": matched_rules,
            "reasons": reasons,
        }

    def _detect_url_rules(
        self, content_text: Optional[str], content_html: Optional[str]
    ) -> List[Dict]:
        """检测URL规则。

        Args:
            content_text: 纯文本内容。
            content_html: HTML内容。

        Returns:
            匹配的URL规则列表。
        """
        if not self._compiled_rules[self.RULE_TYPE_URL]:
            return []

        # 提取URL
        urls = self._extract_urls(content_text, content_html)

        matched_rules = []
        for url in urls:
            for rule in self._compiled_rules[self.RULE_TYPE_URL]:
                try:
                    if rule["pattern"].search(url):
                        matched_rules.append({
                            **rule,
                            "matched_text": url,
                            "rule_type": self.RULE_TYPE_URL,
                        })
                        self._logger.debug(
                            f"URL规则匹配: {rule['name']} 匹配到: {url}"
                        )
                except Exception as e:
                    self._logger.error(f"URL规则检测失败: {e}")

        return matched_rules

    def _detect_sender_rules(self, sender: str) -> List[Dict]:
        """检测发件人规则。

        Args:
            sender: 发件人地址。

        Returns:
            匹配的发件人规则列表。
        """
        if not self._compiled_rules[self.RULE_TYPE_SENDER] or not sender:
            return []

        matched_rules = []
        for rule in self._compiled_rules[self.RULE_TYPE_SENDER]:
            try:
                if rule["pattern"].search(sender):
                    matched_rules.append({
                        **rule,
                        "matched_text": sender,
                        "rule_type": self.RULE_TYPE_SENDER,
                    })
                    self._logger.debug(
                        f"发件人规则匹配: {rule['name']} 匹配到: {sender}"
                    )
            except Exception as e:
                self._logger.error(f"发件人规则检测失败: {e}")

        return matched_rules

    def _detect_content_rules(
        self, subject: Optional[str], content_text: Optional[str]
    ) -> List[Dict]:
        """检测内容规则。

        Args:
            subject: 邮件主题。
            content_text: 纯文本内容。

        Returns:
            匹配的内容规则列表。
        """
        if not self._compiled_rules[self.RULE_TYPE_CONTENT]:
            return []

        # 合并主题和内容
        full_content = ""
        if subject:
            full_content += subject + " "
        if content_text:
            full_content += content_text

        if not full_content.strip():
            return []

        matched_rules = []
        for rule in self._compiled_rules[self.RULE_TYPE_CONTENT]:
            try:
                if rule["pattern"].search(full_content):
                    matched_rules.append({
                        **rule,
                        "matched_text": full_content[:100] + "...",
                        "rule_type": self.RULE_TYPE_CONTENT,
                    })
                    self._logger.debug(
                        f"内容规则匹配: {rule['name']} 匹配到内容"
                    )
            except Exception as e:
                self._logger.error(f"内容规则检测失败: {e}")

        return matched_rules

    def _detect_structure_rules(
        self,
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
    ) -> List[Dict]:
        """检测结构规则。

        Args:
            sender: 发件人。
            content_text: 纯文本内容。
            content_html: HTML内容。

        Returns:
            匹配的结构规则列表。
        """
        if not self._compiled_rules[self.RULE_TYPE_STRUCTURE]:
            return []

        matched_rules = []

        # 检查发件人结构
        if sender:
            for rule in self._compiled_rules[self.RULE_TYPE_STRUCTURE]:
                try:
                    if rule["pattern"].search(sender):
                        matched_rules.append({
                            **rule,
                            "matched_text": sender,
                            "rule_type": self.RULE_TYPE_STRUCTURE,
                        })
                        self._logger.debug(
                            f"结构规则匹配: {rule['name']} 匹配到发件人"
                        )
                except Exception as e:
                    self._logger.error(f"结构规则检测失败: {e}")

        return matched_rules

    def _extract_urls(
        self, content_text: Optional[str], content_html: Optional[str]
    ) -> List[str]:
        """从内容中提取URL。

        Args:
            content_text: 纯文本内容。
            content_html: HTML内容。

        Returns:
            URL列表。
        """
        urls = []

        # 从HTML中提取URL
        if content_html:
            html_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content_html)
            urls.extend(html_urls)

        # 从纯文本中提取URL
        if content_text:
            text_urls = re.findall(r'https?://[^\s]+', content_text)
            urls.extend(text_urls)

        # 去重
        return list(set(urls))

    def _calculate_score(
        self, matched_rules: List[Dict], max_severity: int
    ) -> float:
        """计算钓鱼分数。

        Args:
            matched_rules: 匹配的规则列表。
            max_severity: 最高严重程度。

        Returns:
            钓鱼分数（0-1）。
        """
        if not matched_rules:
            return 0.0

        # 基于匹配规则数量和严重程度计算分数
        rule_count = len(matched_rules)
        base_score = min(rule_count * 0.2, 0.6)  # 规则数量贡献最多0.6

        # 基于最高严重程度计算分数
        severity_score = max_severity / 10.0  # 严重程度贡献最多1.0

        # 综合分数
        final_score = (base_score + severity_score) / 2.0

        return min(final_score, 1.0)