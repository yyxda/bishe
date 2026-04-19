"""JWT认证中间件模块。

提供JWT令牌的生成、验证和刷新功能，用于保护需要认证的API端点。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt


# JWT配置常量
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "argus_jwt_secret_key_2024_secure")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


@dataclass
class JWTPayload:
    """JWT令牌载荷数据类。

    Attributes:
        user_id: 用户ID。
        student_id: 学号。
        display_name: 用户显示名称。
        exp: 过期时间戳。
        token_type: 令牌类型（access/refresh）。
    """

    user_id: int
    student_id: str
    display_name: str
    exp: datetime
    token_type: str = "access"


class JWTAuthMiddleware:
    """JWT认证中间件类。

    负责JWT令牌的生成、验证和刷新操作。
    """

    def __init__(
        self,
        secret_key: str = JWT_SECRET_KEY,
        algorithm: str = JWT_ALGORITHM,
        access_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_days: int = REFRESH_TOKEN_EXPIRE_DAYS,
    ) -> None:
        """初始化JWT认证中间件。

        Args:
            secret_key: JWT签名密钥。
            algorithm: JWT签名算法。
            access_expire_minutes: 访问令牌过期时间（分钟）。
            refresh_expire_days: 刷新令牌过期时间（天）。
        """
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_expire_minutes = access_expire_minutes
        self._refresh_expire_days = refresh_expire_days

    def create_access_token(
        self,
        user_id: int,
        student_id: str,
        display_name: str,
    ) -> str:
        """创建访问令牌。

        Args:
            user_id: 用户ID。
            student_id: 学号。
            display_name: 用户显示名称。

        Returns:
            JWT访问令牌字符串。
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self._access_expire_minutes
        )
        payload = {
            "sub": str(user_id),
            "student_id": student_id,
            "display_name": display_name,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(
        self,
        user_id: int,
        student_id: str,
        display_name: str,
    ) -> str:
        """创建刷新令牌。

        Args:
            user_id: 用户ID。
            student_id: 学号。
            display_name: 用户显示名称。

        Returns:
            JWT刷新令牌字符串。
        """
        expire = datetime.now(timezone.utc) + timedelta(days=self._refresh_expire_days)
        payload = {
            "sub": str(user_id),
            "student_id": student_id,
            "display_name": display_name,
            "exp": expire,
            "type": "refresh",
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str, expected_type: str = "access") -> JWTPayload:
        """验证JWT令牌。

        Args:
            token: JWT令牌字符串。
            expected_type: 期望的令牌类型（access/refresh）。

        Returns:
            解析后的JWT载荷数据。

        Raises:
            HTTPException: 令牌无效或已过期时抛出401错误。
        """
        try:
            payload = jwt.decode(
                token, self._secret_key, algorithms=[self._algorithm]
            )

            token_type = payload.get("type", "access")
            if token_type != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"令牌类型错误，期望{expected_type}，实际{token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_id = int(payload.get("sub", 0))
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌中缺少用户信息",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            exp_timestamp = payload.get("exp")
            exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

            return JWTPayload(
                user_id=user_id,
                student_id=payload.get("student_id", ""),
                display_name=payload.get("display_name", ""),
                exp=exp,
                token_type=token_type,
            )

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"无效的认证令牌: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def refresh_access_token(self, refresh_token: str) -> str:
        """使用刷新令牌获取新的访问令牌。

        Args:
            refresh_token: 刷新令牌字符串。

        Returns:
            新的访问令牌字符串。

        Raises:
            HTTPException: 刷新令牌无效时抛出401错误。
        """
        payload = self.verify_token(refresh_token, expected_type="refresh")
        return self.create_access_token(
            user_id=payload.user_id,
            student_id=payload.student_id,
            display_name=payload.display_name,
        )


# 全局JWT中间件实例
_jwt_middleware = JWTAuthMiddleware()

# HTTPBearer安全方案
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> JWTPayload:
    """FastAPI依赖项：获取当前认证用户。

    从请求的Authorization头中提取JWT令牌并验证，返回用户信息。
    支持Bearer令牌认证方式。

    Args:
        request: FastAPI请求对象。
        credentials: HTTP Bearer认证凭证。

    Returns:
        JWT载荷数据，包含用户信息。

    Raises:
        HTTPException: 未提供令牌或令牌无效时抛出401错误。
    """
    if not credentials:
        # 尝试从Header获取X-User-Id（兼容旧版本）
        user_id_header = request.headers.get("X-User-Id")
        if user_id_header:
            try:
                user_id = int(user_id_header)
                # 兼容模式：返回简化的payload
                return JWTPayload(
                    user_id=user_id,
                    student_id="",
                    display_name="",
                    exp=datetime.now(timezone.utc) + timedelta(hours=1),
                    token_type="legacy",
                )
            except ValueError:
                pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _jwt_middleware.verify_token(credentials.credentials)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[JWTPayload]:
    """FastAPI依赖项：获取可选的当前用户。

    用于既支持认证用户又支持匿名访问的端点。

    Args:
        credentials: HTTP Bearer认证凭证。

    Returns:
        JWT载荷数据或None。
    """
    if not credentials:
        return None

    try:
        return _jwt_middleware.verify_token(credentials.credentials)
    except HTTPException:
        return None


def get_jwt_middleware() -> JWTAuthMiddleware:
    """获取全局JWT中间件实例。

    Returns:
        JWT中间件实例。
    """
    return _jwt_middleware
