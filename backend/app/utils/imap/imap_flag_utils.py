"""IMAP标志位解析工具。"""

from typing import Dict, List, Optional


def normalize_flags(flags: List[str]) -> Optional[str]:
    """规范化flags字符串，便于存储。

    Args:
        flags: 原始flag列表。

    Returns:
        规范化后的flag字符串。
    """
    if not flags:
        return None
    return " ".join(sorted(flags))


def flags_to_status(flags: List[str]) -> Dict[str, bool]:
    """将flags转换为状态字段。

    Args:
        flags: 原始flag列表。

    Returns:
        状态字段映射。
    """
    upper_flags = {flag.upper() for flag in flags}
    return {
        "is_read": "\\SEEN" in upper_flags,
        "is_flagged": "\\FLAGGED" in upper_flags,
        "is_answered": "\\ANSWERED" in upper_flags,
        "is_deleted": "\\DELETED" in upper_flags,
        "is_draft": "\\DRAFT" in upper_flags,
    }
