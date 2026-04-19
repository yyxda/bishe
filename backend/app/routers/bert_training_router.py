"""BERT训练路由 - 使用专业级BERT训练器"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer

from app.middleware.jwt_auth import JWTAuthMiddleware, JWTPayload
from app.utils.phishing.bert_trainer import BERTPhishingTrainer, BERTTrainingConfig
from app.utils.phishing.bert_phishing_detector import BERTPhishingDetector
from app.utils.phishing.phishing_detector_interface import PhishingLevel

logger = logging.getLogger(__name__)
security = HTTPBearer()
jwt_auth = JWTAuthMiddleware()


def get_current_user(credentials = Depends(security)) -> JWTPayload:
    """获取当前用户"""
    token = credentials.credentials
    payload = jwt_auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的令牌")
    return payload

class BERTTrainingRouter:
    """BERT训练路由"""
    
    def __init__(
        self, 
        logger: logging.Logger,
        url_whitelist_matcher=None,
        sender_whitelist_matcher=None
    ) -> None:
        """初始化BERT训练路由。

        Args:
            logger: 日志记录器。
            url_whitelist_matcher: URL白名单匹配器（可选）。
            sender_whitelist_matcher: 发件人白名单匹配器（可选）。
        """
        self._logger = logger
        self._url_whitelist_matcher = url_whitelist_matcher
        self._sender_whitelist_matcher = sender_whitelist_matcher
        self.router = APIRouter(prefix="/api/bert-training", tags=["BERT训练"])
        self._setup_routes()
    
    def _setup_routes(self):
        self.router.add_api_route("/train", self.train_model, methods=["POST"])
        self.router.add_api_route("/status", self.get_training_status, methods=["GET"])
        self.router.add_api_route("/metrics", self.get_model_metrics, methods=["GET"])
        # 添加检测端点
        self.router.add_api_route("/detect", self.detect_text, methods=["POST"])
        self.router.add_api_route("/detect/file", self.detect_file, methods=["POST"])
        # 添加可视化图表端点
        self.router.add_api_route("/visualization/loss", self.get_visualization_loss, methods=["GET"])
        self.router.add_api_route("/visualization/accuracy", self.get_visualization_accuracy, methods=["GET"])
        self.router.add_api_route("/visualization/confusion", self.get_visualization_confusion, methods=["GET"])
        self.router.add_api_route("/visualization/roc", self.get_visualization_roc, methods=["GET"])
        self.router.add_api_route("/visualization/pr", self.get_visualization_pr, methods=["GET"])
        self.router.add_api_route("/visualization/metrics_bar", self.get_visualization_metrics_bar, methods=["GET"])

    async def train_model(self) -> Dict[str, Any]:
        """训练BERT钓鱼邮件检测模型"""
        try:
            backend_root = Path(__file__).resolve().parents[2]
            app_root = backend_root / "app"
            
            # 使用原始数据集
            dataset_path = app_root / "utils/phishing/datasets/chinese_phishing_dataset.csv"
            model_path = app_root / "utils/phishing/ml_models/bert_phishing_model"
            
            # 确保模型目录存在
            model_path.mkdir(parents=True, exist_ok=True)
            
            config = BERTTrainingConfig(
                dataset_path=dataset_path,
                model_path=model_path,
                epochs=2,
                batch_size=8,
                learning_rate=3e-5,
                max_length=128,
                test_size=0.2,
                random_state=42,
                model_name="distilbert-base-multilingual-cased"
            )
            
            trainer = BERTPhishingTrainer(config, logger=self._logger)
            result = trainer.train()
            
            return {
                "status": "success",
                "message": "BERT模型训练完成",
                "metrics": result.get("metrics", {}) if result else {},
                "model_path": str(model_path),
                "visualizations": result.get("visualizations", {}) if result else {},
                "note": "请在.env文件中设置 BERT_MODEL_PATH=" + str(model_path) + " 以启用训练后的模型"
            }
            
        except Exception as e:
            import traceback
            self._logger.error(f"训练失败: {e}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"模型训练失败: {str(e)}")

    async def get_training_status(self, current_user: JWTPayload = Depends(get_current_user)) -> Dict[str, str]:
        """获取训练状态"""
        return {"status": "ready", "message": "模型准备就绪"}
    
    async def get_model_metrics(self, current_user: JWTPayload = Depends(get_current_user)) -> Dict[str, Any]:
        """获取模型性能指标"""
        try:
            import json
            from pathlib import Path
            
            backend_root = Path(__file__).resolve().parents[2]
            app_root = backend_root / "app"
            model_path = app_root / "utils/phishing/ml_models/bert_phishing_model"
            
            if not model_path.exists():
                return {
                    "status": "not_trained",
                    "message": "模型尚未训练",
                    "metrics": None
                }
            
            metrics_file = model_path / "training_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
                return {
                    "status": "trained",
                    "message": "模型已训练",
                    "metrics": metrics
                }
            
            return {
                "status": "trained",
                "message": "模型已训练（无指标文件）",
                "metrics": None
            }
            
        except Exception as e:
            self._logger.error(f"获取指标失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")

    async def get_visualization(
        self, 
        chart_type: str, 
        current_user: JWTPayload = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """获取可视化图表"""
        try:
            import base64
            from pathlib import Path
            
            backend_root = Path(__file__).resolve().parents[2]
            static_path = backend_root / "static" / "visualizations"
            chart_file = static_path / f"{chart_type}.png"
            
            if not chart_file.exists():
                return {
                    "status": "not_found",
                    "message": f"图表 {chart_type} 不存在，请先训练模型",
                    "image": None
                }
            
            # 读取图片并转换为base64
            with open(chart_file, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            
            return {
                "status": "success",
                "message": "图表获取成功",
                "image": img_data
            }
            
        except Exception as e:
            self._logger.error(f"获取可视化图表失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取图表失败: {str(e)}")

    async def get_visualization_loss(self, current_user: JWTPayload = Depends(get_current_user)) -> Dict[str, Any]:
        """获取损失曲线图表"""
        return await self.get_visualization("loss_curve", current_user)

    async def get_visualization_accuracy(self, current_user: JWTPayload = Depends(get_current_user)) -> Dict[str, Any]:
        """获取准确率曲线图表"""
        return await self.get_visualization("accuracy_curve", current_user)

    async def get_visualization_confusion(self, current_user: JWTPayload = Depends(get_current_user)) -> Dict[str, Any]:
        """获取混淆矩阵图表"""
        return await self.get_visualization("confusion_matrix", current_user)

    async def get_visualization_roc(self, current_user: JWTPayload = Depends(get_current_user)) -> Dict[str, Any]:
        """获取ROC曲线图表"""
        return await self.get_visualization("roc_curve", current_user)

    async def get_visualization_pr(self, current_user: JWTPayload = Depends(get_current_user)) -> Dict[str, Any]:
        """获取PR曲线图表"""
        return await self.get_visualization("pr_curve", current_user)

    async def get_visualization_metrics_bar(self, current_user: JWTPayload = Depends(get_current_user)) -> Dict[str, Any]:
        """获取性能指标条形图"""
        return await self.get_visualization("metrics_bar", current_user)

    async def detect_text(
        self, 
        request: Dict[str, str],
        current_user: JWTPayload = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """使用训练后的BERT模型检测文本是否为钓鱼邮件。
        
        Args:
            request: 包含text字段的请求体。
            current_user: 当前用户。
            
        Returns:
            检测结果，包含level、score、reason等字段。
        """
        try:
            text = request.get("text", "")
            sender = request.get("sender", "test@example.com")
            subject = request.get("subject", None)
            
            if not text.strip():
                return {
                    "status": "error",
                    "message": "文本内容不能为空",
                    "result": None
                }
            
            # 1. 检查发件人是否在白名单中
            if self._sender_whitelist_matcher:
                try:
                    from app.utils.whitelist.sender_whitelist_matcher import SenderWhitelistMatcher
                    if await self._sender_whitelist_matcher.is_sender_whitelisted(sender, current_user.user_id):
                        self._logger.info(f"发件人 {sender} 在白名单中，跳过检测")
                        return {
                            "status": "success",
                            "message": "检测完成",
                            "result": {
                                "level": "NORMAL",
                                "score": 0.0,
                                "reason": "发件人在白名单中，无需检测"
                            }
                        }
                except Exception as e:
                    self._logger.error(f"检查发件人白名单失败: {str(e)}", exc_info=True)
            
            # 2. 检查文本中的URL是否都在白名单中
            if self._url_whitelist_matcher:
                try:
                    from app.utils.whitelist.url_whitelist_matcher import UrlWhitelistMatcher
                    urls = set(UrlWhitelistMatcher.extract_urls_from_text(text))
                    
                    if urls:
                        all_whitelisted = await self._url_whitelist_matcher.check_urls_whitelisted(
                            list(urls), current_user.user_id
                        )
                        if all_whitelisted:
                            self._logger.info(
                                f"文本中的所有URL ({len(urls)}个) 都在白名单中，跳过检测"
                            )
                            return {
                                "status": "success",
                                "message": "检测完成",
                                "result": {
                                    "level": "NORMAL",
                                    "score": 0.0,
                                    "reason": f"文本中的所有链接 ({len(urls)}个) 都在白名单中，无需检测"
                                }
                            }
                except Exception as e:
                    self._logger.error(f"检查URL白名单失败: {str(e)}", exc_info=True)
            
            # 3. 执行正常检测
            # 强制使用训练后的模型路径
            model_path = Path("/home/master/my_first_project/Argus/backend/app/utils/phishing/ml_models/bert_phishing_model")
            
            # 检查模型是否存在
            if not model_path.exists():
                return {
                    "status": "error",
                    "message": "模型尚未训练，请先训练模型",
                    "result": None
                }
            
            self._logger.info(f"使用训练后的模型: {model_path}")
            
            # 使用与学生邮箱分类相同的模型
            detector = BERTPhishingDetector(
                logger=self._logger,
                model_path=model_path
            )
            
            # 执行检测
            result = await detector.detect(
                subject=subject,
                sender=sender,
                content_text=text,
                content_html=None
            )
            
            # 转换结果格式
            return {
                "status": "success",
                "message": "检测完成",
                "result": {
                    "level": result.level.value,
                    "score": result.score,
                    "reason": result.reason
                }
            }
            
        except Exception as e:
            import traceback
            self._logger.error(f"文本检测失败: {e}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"文本检测失败: {str(e)}")

    async def detect_file(
        self,
        file: UploadFile = File(...),
        current_user: JWTPayload = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """使用训练后的BERT模型检测文件内容是否为钓鱼邮件。
        
        Args:
            file: 上传的文件。
            current_user: 当前用户。
            
        Returns:
            检测结果，包含level、score、reason等字段。
        """
        try:
            # 读取文件内容
            content = await file.read()
            text = content.decode("utf-8", errors="ignore")
            
            if not text.strip():
                return {
                    "status": "error",
                    "message": "文件内容不能为空",
                    "result": None
                }
            
            # 强制使用训练后的模型路径
            model_path = Path("/home/master/my_first_project/Argus/backend/app/utils/phishing/ml_models/bert_phishing_model")
            
            # 检查模型是否存在
            if not model_path.exists():
                return {
                    "status": "error",
                    "message": "模型尚未训练，请先训练模型",
                    "result": None
                }
            
            self._logger.info(f"使用训练后的模型: {model_path}")
            
            # 使用与学生邮箱分类相同的模型
            detector = BERTPhishingDetector(
                logger=self._logger,
                model_path=model_path
            )
            
            # 执行检测
            result = await detector.detect(
                subject=None,
                sender="test@example.com",
                content_text=text,
                content_html=None
            )
            
            # 转换结果格式
            return {
                "status": "success",
                "message": "检测完成",
                "result": {
                    "level": result.level.value,
                    "score": result.score,
                    "reason": result.reason
                }
            }
            
        except Exception as e:
            import traceback
            self._logger.error(f"文件检测失败: {e}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"文件检测失败: {str(e)}")