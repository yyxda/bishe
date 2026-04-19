"""应用工厂模块。"""

from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import AppConfig
from app.core.container import AppContainer


class AppFactory:
    """FastAPI 应用工厂。

    该工厂用于集中创建应用实例与中间件配置。
    """

    def __init__(self, container: AppContainer, config: AppConfig) -> None:
        """初始化应用工厂。

        Args:
            container: 依赖容器。
            config: 应用配置。
        """
        self._container = container
        self._config = config

    def create_app(self) -> FastAPI:
        """创建 FastAPI 应用实例。

        Returns:
            FastAPI 应用。
        """
        app = FastAPI(title=self._config.app_name)
        self._configure_middleware(app)
        
        # 挂载静态文件目录
        backend_root = Path(__file__).resolve().parents[3]
        static_dir = backend_root / "backend" / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        app.include_router(self._container.auth_router.router)
        app.include_router(self._container.email_account_router.router)
        app.include_router(self._container.email_router.router)
        app.include_router(self._container.phishing_router.router)
        app.include_router(self._container.admin_router.router)
        app.include_router(self._container.bert_training_router.router)
        app.include_router(self._container.phishing_rule_router.router)
        app.get("/")(self._health_check)
        app.get("/api/health")(self._health_check)
        return app

    def _configure_middleware(self, app: FastAPI) -> None:
        """配置中间件。

        Args:
            app: FastAPI 应用实例。
        """
        allow_origins = self._config.cors_origins
        allow_credentials = True
        if self._config.cors_allow_all:
            # 开发期允许所有来源，避免跨域预检失败。
            allow_origins = ["*"]
            allow_credentials = False

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    async def _health_check(self) -> Dict[str, str]:
        """应用健康检查接口。

        Returns:
            简单的健康状态响应。
        """
        return {"status": "ok"}