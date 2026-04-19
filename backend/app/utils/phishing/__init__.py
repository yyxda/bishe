"""钓鱼检测工具模块。"""

from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingResult,
    PhishingLevel,
)
from app.utils.phishing.bert_phishing_detector import BERTPhishingDetector
from app.utils.phishing.hybrid_phishing_detector import HybridPhishingDetector
from app.utils.phishing.bert_trainer import BERTPhishingTrainer, BERTTrainingConfig
from app.utils.phishing.url_detector import LongUrlDetector
from app.utils.phishing.composite_detector import CompositePhishingDetector
from app.utils.phishing.dynamic_detector import DynamicPhishingDetector
from app.utils.phishing.score_level_mapper import ScoreLevelMapper, ScoreThresholds

__all__ = [
    "PhishingDetectorInterface",
    "PhishingResult",
    "PhishingLevel",
    "BERTPhishingDetector",
    "HybridPhishingDetector",
    "BERTPhishingTrainer",
    "BERTTrainingConfig",
    "ScoreLevelMapper",
    "ScoreThresholds",
    "LongUrlDetector",
    "CompositePhishingDetector",
    "DynamicPhishingDetector",
]