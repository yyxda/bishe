"""训练钓鱼邮件检测模型的脚本。"""

from __future__ import annotations

import sys
import logging
from pathlib import Path

# 确保以脚本方式执行时能正确导入backend下的app模块。
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.utils.phishing import MLPhishingTrainer, MLTrainingConfig


def main() -> None:
    """训练并保存模型。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger = logging.getLogger("phishing_train")

    app_root = BACKEND_ROOT / "app"
    dataset_path = app_root / "utils/phishing/datasets/spam_assassin.csv"
    model_path = app_root / "utils/phishing/ml_models/phishing_model.h5"
    artifacts_dir = app_root / "utils/phishing/ml_models/artifacts"
    vectorizer_path = app_root / "utils/phishing/ml_models/tfidf_vectorizer.joblib"

    config = MLTrainingConfig(
        dataset_path=dataset_path,
        model_path=model_path,
        artifacts_dir=artifacts_dir,
        vectorizer_path=vectorizer_path,
    )
    trainer = MLPhishingTrainer(config, logger=logger)
    metrics = trainer.train()

    logger.info("训练完成，评估指标: %s", metrics)


if __name__ == "__main__":
    main()
