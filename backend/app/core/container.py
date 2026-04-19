"""依赖容器模块。"""

from app.core.config import AppConfig
from app.core.database import DatabaseManager
from app.crud.user_crud import UserCrud
from app.crud.email_crud import EmailCrud
from app.crud.email_account_crud import EmailAccountCrud
from app.crud.email_sync_crud import EmailSyncCrud
from app.crud.mailbox_crud import MailboxCrud
from app.crud.url_whitelist_crud import UrlWhitelistCrud
from app.crud.sender_whitelist_crud import SenderWhitelistCrud
from app.crud.system_settings_crud import SystemSettingsCrud
from app.crud.phishing_rule_crud import PhishingRuleCrud
from app.middleware.jwt_auth import JWTAuthMiddleware
from app.routers.auth_router import AuthRouter
from app.routers.email_account_router import EmailAccountRouter
from app.routers.email_router import EmailRouter
from app.routers.phishing_router import PhishingRouter
from app.routers.admin_router import AdminRouter
from app.routers.bert_training_router import BERTTrainingRouter
from app.routers.phishing_rule_router import PhishingRuleRouter
from app.services.auth_service import AuthService
from app.services.email_account_service import EmailAccountService
from app.services.email_service import EmailService
from app.services.phishing_detection_service import PhishingDetectionService
from app.services.phishing_event_service import PhishingEventService
from app.services.admin_service import AdminService
from app.services.url_whitelist_service import UrlWhitelistMatcher
from app.services.sender_whitelist_service import SenderWhitelistMatcher
from app.services.system_settings_service import SystemSettingsService
from app.services.phishing_rule_service import PhishingRuleService
from app.utils.logging.logger_factory import LoggerFactory
from app.utils.password_hasher import PasswordHasher
from app.utils.validators import AuthValidator
from app.utils.crypto.password_encryptor import PasswordEncryptor
from app.utils.phishing import (
    HybridPhishingDetector,
    LongUrlDetector,
    DynamicPhishingDetector,
)


class AppContainer:
    """应用依赖容器。

    该容器集中管理可复用的服务与工具类实例。
    """

    def __init__(self, config: AppConfig) -> None:
        """初始化依赖容器。

        Args:
            config: 应用配置。
        """
        self._config = config
        self._logger_factory = LoggerFactory()

        # 数据库管理器
        self.db_manager = DatabaseManager(config.get_database_url())

        # 工具类
        self.password_hasher = PasswordHasher()
        self.jwt_middleware = JWTAuthMiddleware()
        self.validator = AuthValidator()
        self.password_encryptor = PasswordEncryptor()

        # 系统设置与钓鱼检测器
        self._init_system_settings()
        self._init_phishing_rules()  # 先初始化规则检测器
        self._init_phishing_detectors()  # 再初始化钓鱼检测器（依赖规则检测器）

        # 钓鱼检测事件推送服务
        self.phishing_event_service = PhishingEventService(
            logger=self._logger_factory.create_logger("app.services.phishing_event")
        )

        # 初始化CRUD、服务、路由层
        self._init_whitelist_components()  # 先初始化白名单基础组件
        self._init_email_account_layer()  # 初始化邮件和钓鱼检测（依赖白名单基础组件）
        self._init_user_layer()  # 初始化用户认证服务（依赖邮箱账户服务）
        self._init_admin_service_and_router()  # 初始化管理员服务（依赖邮件和钓鱼检测服务）
        self._init_email_layer()
        self._init_phishing_layer()
        self._init_bert_training_layer()

    def _init_user_layer(self) -> None:
        """初始化用户相关的CRUD、服务和路由。"""
        # CRUD层
        self.user_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.user", "用户"
        )
        self.user_crud = UserCrud(
            self.db_manager, self.password_hasher, self.user_crud_logger
        )

        # 服务层
        self.auth_logger = self._logger_factory.create_logger("app.services.auth")
        self.auth_service = AuthService(
            self.user_crud,
            self.validator,
            self.password_hasher,
            self.jwt_middleware,
            self.db_manager,
            self.user_crud_logger,
            self.auth_logger,
            self.email_account_service,  # 注入邮箱账户服务
        )

        # 路由层
        self.auth_router_logger = self._logger_factory.create_logger("app.routers.auth")
        self.auth_router = AuthRouter(
            self.auth_service, self._config, self.auth_router_logger
        )

    def _init_email_account_layer(self) -> None:
        """初始化邮箱账户相关的CRUD、服务和路由。"""
        # CRUD层
        self.email_account_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.email_account", "邮箱账户"
        )
        self.email_account_crud = EmailAccountCrud(
            self.db_manager,
            self.password_encryptor,
            self.email_account_crud_logger,
        )

        # 邮件CRUD（邮箱账户服务需要）
        self.email_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.email", "邮件"
        )
        self.email_crud = EmailCrud(
            self.db_manager,
            self.email_crud_logger,
        )

        # 文件夹CRUD
        self.mailbox_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.mailbox", "邮箱文件夹"
        )
        self.mailbox_crud = MailboxCrud(
            self.db_manager,
            self.mailbox_crud_logger,
        )

        # 同步写入CRUD
        self.email_sync_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.email_sync", "邮件同步"
        )
        self.email_sync_crud = EmailSyncCrud(
            self.db_manager,
            self.email_sync_crud_logger,
        )

        # 钓鱼检测服务（需要白名单匹配器，在admin_layer初始化后使用）
        self.phishing_detection_logger = self._logger_factory.create_logger(
            "app.services.phishing_detection"
        )
        self.phishing_detection_service = PhishingDetectionService(
            email_crud=self.email_crud,
            phishing_detector=self.phishing_detector,
            event_service=self.phishing_event_service,
            url_whitelist_matcher=self.url_whitelist_matcher,
            sender_whitelist_matcher=self.sender_whitelist_matcher,
            system_settings_service=self.system_settings_service,
            rule_based_detector=self.rule_based_detector,
            logger=self.phishing_detection_logger,
        )

        # 服务层
        self.email_account_logger = self._logger_factory.create_logger(
            "app.services.email_account"
        )
        self.email_account_service = EmailAccountService(
            self.email_account_crud,
            self.mailbox_crud,
            self.email_sync_crud,
            self.phishing_detector,
            self.phishing_detection_service,
            self.email_account_logger,
        )

        # 路由层
        self.email_account_router_logger = self._logger_factory.create_logger(
            "app.routers.email_account"
        )
        self.email_account_router = EmailAccountRouter(
            self.email_account_service,
            self._config,
            self.email_account_router_logger,
        )

    def _init_email_layer(self) -> None:
        """初始化邮件相关的服务和路由。"""
        # 服务层
        self.email_logger = self._logger_factory.create_logger("app.services.email")
        self.email_service = EmailService(
            self.email_crud,
            self.email_account_crud,
            self.mailbox_crud,
            self.email_logger,
        )

        # 路由层
        self.email_router_logger = self._logger_factory.create_logger(
            "app.routers.email"
        )
        self.email_router = EmailRouter(
            self.email_service,
            self.phishing_detection_service,
            self.admin_service,
            self._config,
            self.email_router_logger,
        )

    def _init_phishing_layer(self) -> None:
        """初始化钓鱼检测相关路由。"""
        self.phishing_router = PhishingRouter(
            phishing_detector=self.phishing_detector,
            event_service=self.phishing_event_service,
        )

    def _init_bert_training_layer(self) -> None:
        """初始化BERT训练相关路由。"""
        self.bert_training_logger = self._logger_factory.create_logger(
            "app.routers.bert_training"
        )
        self.bert_training_router = BERTTrainingRouter(
            logger=self.bert_training_logger,
            url_whitelist_matcher=self.url_whitelist_matcher,
            sender_whitelist_matcher=self.sender_whitelist_matcher
        )

    async def close(self) -> None:
        """关闭容器中的资源。"""
        await self.db_manager.close()

    def _init_whitelist_components(self) -> None:
        """初始化白名单相关的CRUD和匹配器（供其他层使用）。"""
        # CRUD层 - URL白名单
        self.url_whitelist_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.url_whitelist", "URL白名单"
        )
        self.url_whitelist_crud = UrlWhitelistCrud(
            self.db_manager,
            self.url_whitelist_crud_logger,
        )

        # CRUD层 - 发件人白名单
        self.sender_whitelist_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.sender_whitelist", "发件人白名单"
        )
        self.sender_whitelist_crud = SenderWhitelistCrud(
            self.db_manager,
            self.sender_whitelist_crud_logger,
        )

        # 白名单匹配器
        self.url_whitelist_matcher = UrlWhitelistMatcher(
            self.url_whitelist_crud,
            self._logger_factory.create_logger("app.services.url_whitelist"),
        )
        
        self.sender_whitelist_matcher = SenderWhitelistMatcher(
            self.sender_whitelist_crud,
            self._logger_factory.create_logger("app.services.sender_whitelist"),
        )

    def _init_system_settings(self) -> None:
        """初始化系统设置相关的CRUD和服务。"""
        self.system_settings_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.system_settings", "系统设置"
        )
        self.system_settings_crud = SystemSettingsCrud(
            self.db_manager,
            self.system_settings_crud_logger,
        )
        self.system_settings_logger = self._logger_factory.create_logger(
            "app.services.system_settings"
        )
        self.system_settings_service = SystemSettingsService(
            self.system_settings_crud,
            self.system_settings_logger,
        )

    def _init_phishing_rules(self) -> None:
        """初始化钓鱼检测规则相关的CRUD、服务和路由。"""
        # CRUD层
        self.phishing_rule_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.phishing_rule", "钓鱼检测规则"
        )
        self.phishing_rule_crud = PhishingRuleCrud(
            self.db_manager,
            self.phishing_rule_crud_logger,
        )

        # 服务层
        self.phishing_rule_logger = self._logger_factory.create_logger(
            "app.services.phishing_rule"
        )
        self.phishing_rule_service = PhishingRuleService(
            self.phishing_rule_crud,
            self.phishing_rule_logger,
        )

        # 路由层
        self.phishing_rule_router_logger = self._logger_factory.create_logger(
            "app.routers.phishing_rule"
        )
        self.phishing_rule_router = PhishingRuleRouter(
            self.phishing_rule_service,
            self.phishing_rule_router_logger,
        )

        # 规则检测器（用于混合检测）
        from app.utils.phishing.rule_based_detector import RuleBasedPhishingDetector
        self.rule_based_detector_logger = self._logger_factory.create_logger(
            "app.utils.phishing.rule_based_detector"
        )
        self.rule_based_detector = RuleBasedPhishingDetector(
            rules=[],
            logger=self.rule_based_detector_logger,
        )

    def _init_phishing_detectors(self) -> None:
        """初始化钓鱼检测器 - 根据配置决定使用BERT还是混合检测器"""
        phishing_logger = self._logger_factory.create_logger("app.utils.phishing")
        
        # 强制使用训练后的模型路径
        from pathlib import Path
        model_path = Path("/home/master/my_first_project/Argus/backend/app/utils/phishing/ml_models/bert_phishing_model")
        phishing_logger.info(f"强制使用训练后的模型: {model_path}")
        
        # 根据配置决定使用哪种检测器
        if self._config.enable_rule_based_detection:
            # 使用混合检测器（BERT + 规则）
            from app.utils.phishing.hybrid_phishing_detector import HybridPhishingDetector
            self.phishing_detector = HybridPhishingDetector(
                logger=phishing_logger,
                model_path=model_path,
                enable_rule_based_detection=True,
                rule_based_detector=self.rule_based_detector
            )
            phishing_logger.info("使用混合检测器（BERT + 规则检测）")
        else:
            # 使用纯BERT检测器
            from app.utils.phishing.bert_phishing_detector import BERTPhishingDetector
            self.phishing_detector = BERTPhishingDetector(
                logger=phishing_logger,
                model_path=model_path
            )
            phishing_logger.info("使用纯BERT检测器（规则检测已禁用）")

    def _init_admin_service_and_router(self) -> None:
        """初始化管理员相关的服务和路由。"""
        # 服务层
        self.admin_logger = self._logger_factory.create_logger("app.services.admin")
        self.admin_service = AdminService(
            self.user_crud,
            self.url_whitelist_crud,
            self.sender_whitelist_crud,
            self.system_settings_service,
            self.email_crud,
            self.phishing_detection_service,
            self.admin_logger,
        )

        # 路由层
        self.admin_router_logger = self._logger_factory.create_logger(
            "app.routers.admin"
        )
        self.admin_router = AdminRouter(
            self.admin_service,
            self._config,
            self.admin_router_logger,
        )