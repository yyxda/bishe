"""认证服务层。"""

import logging
import asyncio

from app.core.database import DatabaseManager
from app.crud.user_crud import UserCrud
from app.middleware.jwt_auth import JWTAuthMiddleware
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.services.email_account_service import EmailAccountService
from app.utils.password_hasher import PasswordHasher
from app.utils.validators import AuthValidator


class AuthService:
    """认证服务类。

    该服务类负责登录流程编排与核心业务校验。
    """

    def __init__(
        self,
        user_crud: UserCrud,
        validator: AuthValidator,
        password_hasher: PasswordHasher,
        jwt_middleware: JWTAuthMiddleware,
        db_manager: DatabaseManager,
        crud_logger: logging.Logger,
        logger: logging.Logger,
        email_account_service: EmailAccountService,
    ) -> None:
        """初始化认证服务。

        Args:
            user_crud: 用户数据访问对象。
            validator: 登录校验器。
            password_hasher: 密码哈希工具。
            jwt_middleware: JWT认证中间件。
            db_manager: 数据库管理器。
            crud_logger: CRUD日志记录器。
            logger: 日志记录器。
            email_account_service: 邮箱账户服务。
        """
        self._user_crud = user_crud
        self._validator = validator
        self._password_hasher = password_hasher
        self._jwt_middleware = jwt_middleware
        self._db_manager = db_manager
        self._crud_logger = crud_logger
        self._logger = logger
        self._email_account_service = email_account_service

    async def login(self, request: LoginRequest) -> LoginResponse:
        try:
            email = request.student_id
            password = request.password or ''
            email_type = request.email_type or 'qq'
            auth_code = request.auth_code or ''
            
            login_code = auth_code or password
            
            if not login_code:
                return LoginResponse(success=False, message="请输入密码或授权码")
            
            # 转换邮箱类型为大写，匹配后端枚举
            email_type_map = {
                'qq': 'QQ',
                '163': 'NETEASE',
                '126': 'NETEASE',
                'netease': 'NETEASE',
                'default': 'DEFAULT',
                'custom': 'CUSTOM',
            }
            email_type_str = email_type_map.get(email_type.lower(), 'QQ')
            
            # 转换为 EmailType 枚举
            from app.entities.email_account_entity import EmailType
            try:
                email_type = EmailType[email_type_str]
            except KeyError:
                email_type = EmailType.QQ
            
            user = None
            account_id = None  # 初始化 account_id，避免管理员登录时未定义
            
            # 管理员登录：用student_id查找
            if email == 'Administrator':
                self._logger.info("[管理员登录] student_id=%s", email)
                user = await self._user_crud.get_by_student_id(email)
                if not user:
                    # 自动创建管理员
                    self._logger.info("[管理员登录] 创建新管理员")
                    user = await self._user_crud.create(email, login_code, email)
                else:
                    # 验证密码
                    if not self._password_hasher.verify(login_code, user.password_hash):
                        return LoginResponse(success=False, message="密码错误")
            else:
                # 学生登录：用email查找
                full_email = email if '@' in email else f"{email}@{email_type}.com"
                self._logger.info("[学生登录] full_email=%s", full_email)
                user = await self._user_crud.get_by_email(full_email)
                if not user:
                    display = email.split('@')[0] if '@' in email else email
                    self._logger.info("[学生登录] 创建新用户: display=%s", display)
                    user = await self._user_crud.create(display, login_code, display,
                        email=full_email, email_type=email_type, auth_code=login_code)
                
                # 检查用户是否已有邮箱账户
                try:
                    from app.crud.email_account_crud import EmailAccountCrud
                    from app.utils.crypto.password_encryptor import PasswordEncryptor
                    from app.schemas.email_account_schema import AddEmailAccountRequest
                    from app.utils.imap.imap_config import ImapConfigFactory
                    
                    email_account_crud = EmailAccountCrud(
                        self._db_manager,
                        PasswordEncryptor(),
                        self._crud_logger
                    )
                    
                    # 查询用户的邮箱账户
                    existing_accounts = await email_account_crud.get_by_user_id(user.id)
                    
                    account_id = None
                    if not existing_accounts:
                        # 没有邮箱账户，创建一个
                        self._logger.info("[学生登录] 用户没有邮箱账户，开始创建...")
                        
                        config = ImapConfigFactory.get_config_or_default(
                            email_type=email_type
                        )
                        
                        # 使用 EmailAccountService 创建邮箱账户
                        try:
                            add_request = AddEmailAccountRequest(
                                email_address=full_email,
                                email_type=email_type,
                                auth_password=login_code,
                                imap_host=config.imap_host,
                                imap_port=config.imap_port,
                                smtp_host=config.smtp_host,
                                smtp_port=config.smtp_port,
                                use_ssl=config.use_ssl
                            )
                            
                            add_response = await self._email_account_service.add_email_account(
                                user.id, add_request
                            )
                            
                            if add_response.success:
                                account_id = add_response.account_id
                                self._logger.info("[学生登录] 自动创建邮箱账户成功: %s", full_email)
                            else:
                                self._logger.error("[学生登录] 创建邮箱账户失败: %s", add_response.message)
                                # 即使创建失败，也继续登录流程，让用户手动添加邮箱账户
                                self._logger.warning("[学生登录] 邮箱账户创建失败，用户需要手动添加邮箱账户")
                        except Exception as e:
                            self._logger.error("[学生登录] 创建邮箱账户失败: %s", str(e), exc_info=True)
                            # 即使创建失败，也继续登录流程，让用户手动添加邮箱账户
                            self._logger.warning("[学生登录] 邮箱账户创建失败，用户需要手动添加邮箱账户")
                    else:
                        account_id = existing_accounts[0].id
                    
                    # 自动同步邮件（后台异步）
                    if account_id:
                        self._logger.info("[学生登录] 启动后台自动同步邮件...")
                        # 重置邮箱账户的last_uid，确保同步所有邮件
                        try:
                            await self._email_account_service.reset_sync_state(user.id, account_id)
                            self._logger.info("[学生登录] 已重置同步状态，将同步所有邮件")
                        except Exception as e:
                            self._logger.warning("[学生登录] 重置同步状态失败: %s", str(e))
                        
                        # 启动后台异步任务进行邮件同步，不阻塞登录响应
                        try:
                            asyncio.create_task(self._sync_emails_async(user.id, account_id))
                            self._logger.info("[学生登录] 后台同步任务已启动")
                        except Exception as e:
                            self._logger.error("[学生登录] 启动后台同步任务失败: %s", str(e))
                
                except Exception as e:
                    self._logger.error("[学生登录] 检查/创建邮箱账户失败: %s", str(e), exc_info=True)
            
            if not user.is_active:
                return LoginResponse(success=False, message="账号已被停用")
            
            access_token = self._jwt_middleware.create_access_token(user.id, user.student_id, user.display_name)
            refresh_token = self._jwt_middleware.create_refresh_token(user.id, user.student_id, user.display_name)
            return LoginResponse(success=True, message="登录成功", token=access_token, refresh_token=refresh_token, user_id=user.id, student_id=user.student_id, display_name=user.display_name, role=user.role, email_account_id=account_id)
        except Exception as e:
            self._logger.error("[登录异常] 错误: %s, 类型: %s", str(e), type(e).__name__, exc_info=True)
            return LoginResponse(success=False, message=f"登录失败: {str(e)}")

    async def _sync_emails_async(self, user_id: int, account_id: int) -> None:
        """后台异步同步邮件。

        Args:
            user_id: 用户ID。
            account_id: 邮箱账户ID。
        """
        try:
            self._logger.info("[后台同步] 开始同步邮箱账户: user_id=%d, account_id=%d", user_id, account_id)
            result = await self._email_account_service.sync_emails(user_id, account_id)
            if result.success:
                self._logger.info("[后台同步] 同步完成: %s", result.message)
            else:
                self._logger.warning("[后台同步] 同步失败: %s", result.message)
        except Exception as e:
            self._logger.error("[后台同步] 同步异常: %s", str(e), exc_info=True)

    async def refresh_token(self, request: RefreshTokenRequest) -> RefreshTokenResponse:
        """刷新访问令牌。

        Args:
            request: 刷新令牌请求模型。

        Returns:
            刷新令牌响应模型。
        """
        try:
            new_token = self._jwt_middleware.refresh_access_token(request.refresh_token)
            return RefreshTokenResponse(
                success=True,
                message="令牌刷新成功。",
                token=new_token,
            )
        except Exception as e:
            self._logger.warning("令牌刷新失败: %s", str(e))
            return RefreshTokenResponse(
                success=False,
                message="令牌刷新失败，请重新登录。",
            )