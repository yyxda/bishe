"""认证相关的请求与响应模型。"""

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求模型。"""

    student_id: str = Field(..., min_length=1, description="邮箱账号")
    password: str = Field(default="", description="密码或备用授权码")
    email_type: str = Field(default="qq", description="邮箱类型: qq, 163, netease等")
    auth_code: str = Field(default="", description="授权码")


class LoginResponse(BaseModel):
    """登录响应模型。"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
    token: Optional[str] = Field(default=None, description="访问令牌")
    refresh_token: Optional[str] = Field(default=None, description="刷新令牌")
    user_id: Optional[int] = Field(default=None, description="用户ID")
    student_id: Optional[str] = Field(default=None, description="学号")
    display_name: Optional[str] = Field(default=None, description="显示名称")
    role: Optional[str] = Field(default=None, description="用户角色")
    email_account_id: Optional[int] = Field(default=None, description="邮箱账户ID")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型。"""

    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模型。"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
    token: Optional[str] = Field(default=None, description="新访问令牌")


class UserInfoResponse(BaseModel):
    """用户信息响应模型。"""

    success: bool = Field(default=True, description="是否成功")
    user_id: int = Field(..., description="用户ID")
    student_id: str = Field(..., description="学号")
    display_name: str = Field(..., description="显示名称")