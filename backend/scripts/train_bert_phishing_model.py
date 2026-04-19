"""BERT钓鱼邮件检测模型训练脚本。

使用中文钓鱼邮件数据集训练BERT模型。
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)


class PhishingEmailDataset(Dataset):
    """钓鱼邮件数据集类。"""

    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 512):
        """初始化数据集。

        Args:
            texts: 文本列表。
            labels: 标签列表。
            tokenizer: 分词器。
            max_length: 最大长度。
        """
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(label, dtype=torch.long),
        }


class BERTPhishingTrainer:
    """BERT钓鱼邮件检测模型训练器。"""

    def __init__(
        self,
        model_name: str = "bert-base-chinese",
        output_dir: str = "./models",
        max_length: int = 512,
        batch_size: int = 16,
        num_epochs: int = 3,
        learning_rate: float = 2e-5,
        logger: logging.Logger = None,
    ):
        """初始化训练器。

        Args:
            model_name: 预训练模型名称。
            output_dir: 输出目录。
            max_length: 最大文本长度。
            batch_size: 批次大小。
            num_epochs: 训练轮数。
            learning_rate: 学习率。
            logger: 日志记录器。
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.max_length = max_length
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化tokenizer和模型
        self.tokenizer = None
        self.model = None

    def load_data(self, dataset_path: str) -> Dict[str, List]:
        """加载数据集。

        Args:
            dataset_path: 数据集路径。

        Returns:
            数据字典。
        """
        self.logger.info(f"正在加载数据集: {dataset_path}")

        df = pd.read_csv(dataset_path)
        df = df.dropna()

        # 合并主题和内容
        df["text"] = df["subject"] + " " + df["content"]

        texts = df["text"].tolist()
        labels = df["target"].tolist()

        self.logger.info(f"数据集加载完成: {len(texts)} 条样本")
        self.logger.info(f"钓鱼邮件: {sum(labels)} 条")
        self.logger.info(f"正常邮件: {len(labels) - sum(labels)} 条")

        return {"texts": texts, "labels": labels}

    def prepare_model(self):
        """准备模型和tokenizer。"""
        self.logger.info(f"正在加载预训练模型: {self.model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=2,  # 二分类：正常/钓鱼
        )

        self.logger.info("模型和tokenizer加载完成")

    def train(self, dataset_path: str, test_size: float = 0.2):
        """训练模型。

        Args:
            dataset_path: 数据集路径。
            test_size: 测试集比例。
        """
        from sklearn.model_selection import train_test_split

        # 加载数据
        data = self.load_data(dataset_path)
        texts = data["texts"]
        labels = data["labels"]

        # 划分训练集和测试集
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=test_size, random_state=42
        )

        # 准备模型
        self.prepare_model()

        # 创建数据集
        train_dataset = PhishingEmailDataset(
            train_texts, train_labels, self.tokenizer, self.max_length
        )
        val_dataset = PhishingEmailDataset(
            val_texts, val_labels, self.tokenizer, self.max_length
        )

        # 训练参数
        training_args = TrainingArguments(
            output_dir=str(self.output_dir / "checkpoints"),
            num_train_epochs=self.num_epochs,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=10,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            learning_rate=self.learning_rate,
            save_total_limit=2,
        )

        # 创建Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        )

        # 开始训练
        self.logger.info("开始训练模型...")
        trainer.train()

        # 评估模型
        self.logger.info("评估模型...")
        eval_results = trainer.evaluate()
        self.logger.info(f"评估结果: {eval_results}")

        # 保存最终模型
        final_model_path = self.output_dir / "final_model"
        trainer.save_model(str(final_model_path))
        self.tokenizer.save_pretrained(str(final_model_path))

        self.logger.info(f"模型已保存到: {final_model_path}")

        return eval_results

    def evaluate(self, dataset_path: str):
        """评估模型。

        Args:
            dataset_path: 数据集路径。
        """
        from sklearn.metrics import classification_report, confusion_matrix

        # 加载数据
        data = self.load_data(dataset_path)
        texts = data["texts"]
        labels = data["labels"]

        # 创建数据集
        dataset = PhishingEmailDataset(
            texts, labels, self.tokenizer, self.max_length
        )

        # 创建DataLoader
        dataloader = DataLoader(dataset, batch_size=self.batch_size)

        # 预测
        self.model.eval()
        predictions = []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"]
                attention_mask = batch["attention_mask"]

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=-1)
                predictions.extend(preds.cpu().numpy())

        # 计算指标
        report = classification_report(labels, predictions, target_names=["正常", "钓鱼"])
        cm = confusion_matrix(labels, predictions)

        self.logger.info("\n分类报告:\n%s", report)
        self.logger.info("\n混淆矩阵:\n%s", cm)

        return report, cm


def main():
    """主函数。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # 配置
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else "chinese_phishing_dataset.csv"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./bert_phishing_model"

    # 创建训练器
    trainer = BERTPhishingTrainer(
        model_name="bert-base-chinese",
        output_dir=output_dir,
        max_length=512,
        batch_size=8,  # 根据GPU内存调整
        num_epochs=3,
        learning_rate=2e-5,
        logger=logger,
    )

    # 训练模型
    trainer.train(dataset_path)

    # 评估模型
    trainer.evaluate(dataset_path)

    logger.info("训练完成！")


if __name__ == "__main__":
    main()