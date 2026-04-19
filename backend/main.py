"""应用入口模块（供 uvicorn CLI 使用）。"""

from app.main import app

__all__ = ["app"]

# TODO 重构抓取邮件机制，仿照Gmail邮箱来存储，高存储，高并发
