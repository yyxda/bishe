"""表单校验工具。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """校验结果。

    Attributes:
        is_valid: 校验是否通过。
        message: 校验失败时的提示信息。
    """

    is_valid: bool
    message: str


class AuthValidator:
    """登录校验器。

    该校验器用于保证学号与密码的基本格式正确。
    """

    def validate_login(self, student_id: str, password: str) -> ValidationResult:
        """校验登录参数。

        Args:
            student_id: 学号/账号。
            password: 密码。

        Returns:
            校验结果。
        """
        if not student_id or not password:
            return ValidationResult(False, "请输入账号和密码。")

        if not student_id.isalnum():
            return ValidationResult(False, "账号应为字母或数字。")

        if len(student_id) < 3 or len(student_id) > 20:
            return ValidationResult(False, "账号长度应为 3-20 位。")

        if len(password) < 6:
            return ValidationResult(False, "密码长度至少为 6 位。")

        return ValidationResult(True, "")
