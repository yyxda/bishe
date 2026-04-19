"""系统健康检查路由"""

import logging
from fastapi import APIRouter
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HealthRouter:
    """系统健康检查路由"""
    
    def __init__(self, logger: logging.Logger) -> None:
        """初始化健康检查路由。

        Args:
            logger: 日志记录器。
        """
        self._logger = logger
        self.router = APIRouter(prefix="/api", tags=["系统健康"])
        self._setup_routes()
    
    def _setup_routes(self):
        self.router.add_api_route("/health", self.health_check, methods=["GET"])
        self.router.add_api_route("/system-status", self.system_status, methods=["GET"])

    async def health_check(self) -> Dict[str, str]:
        """基础健康检查接口"""
        return {
            "status": "healthy",
            "message": "系统运行正常",
            "timestamp": "2024-01-01T00:00:00Z"  # 实际应该用datetime.now()
        }
    
    async def system_status(self) -> Dict[str, Any]:
        """系统状态检查"""
        try:
            # 检查各个组件状态
            from app.utils.phishing.bert_phishing_detector import BERTPhishingDetector
            from app.utils.phishing.hybrid_phishing_detector import HybridPhishingDetector
            from pathlib import Path
            
            # 强制使用训练后的模型路径
            model_path = Path("/home/master/my_first_project/Argus/backend/app/utils/phishing/ml_models/bert_phishing_model")
            
            # 测试BERT检测器状态
            bert_detector = BERTPhishingDetector(model_path=model_path)
            bert_status = "loaded" if bert_detector._is_loaded else "not_loaded"
            
            # 测试混合检测器状态
            hybrid_detector = HybridPhishingDetector()
            hybrid_status = "ready"
            
            return {
                "status": "healthy",
                "components": {
                    "bert_detector": bert_status,
                    "hybrid_detector": hybrid_status,
                    "database": "connected",  # 需要实际检查
                    "email_sync": "ready"
                },
                "recommendations": [
                    "系统运行正常，可以开始使用"
                ]
            }
            
        except Exception as e:
            self._logger.error(f"系统状态检查失败: {e}")
            return {
                "status": "degraded",
                "message": f"系统部分功能异常: {str(e)}",
                "recommendations": [
                    "请检查网络连接",
                    "尝试重新登录",
                    "如问题持续，请联系管理员"
                ]
            }