"""基于BERT的钓鱼邮件模型训练器模块。

针对中文钓鱼邮件场景优化，使用bert-base-chinese预训练模型进行微调。
"""

import base64
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from torch.utils.data import Dataset
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class ProgressCallback:
    """训练进度回调类。
    
    提供实时训练进度反馈和早停机制。
    """
    
    def __init__(self, logger: logging.Logger):
        """初始化回调。
        
        Args:
            logger: 日志记录器。
        """
        self._logger = logger
        self._best_f1 = 0.0
        self._patience = 3
        self._no_improve_count = 0
    
    def __call__(self, *args, **kwargs):
        """回调函数入口。
        
        Args:
            *args: 可变参数。
            **kwargs: 关键字参数。
        """
        return self
    
    def on_init_end(self, args, state, control, **kwargs):
        """训练初始化完成回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        self._logger.info("训练初始化完成，开始训练...")
    
    def on_train_begin(self, args, state, control, **kwargs):
        """训练开始回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        self._logger.info("训练开始！")
    
    def on_epoch_begin(self, args, state, control, **kwargs):
        """epoch开始回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        self._logger.info(f"开始第 {state.epoch + 1} 轮训练...")
    
    def on_epoch_end(self, args, state, control, **kwargs):
        """epoch结束回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        self._logger.info(f"第 {state.epoch + 1} 轮训练完成")
    
    def on_step_begin(self, args, state, control, **kwargs):
        """step开始回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        pass  # 不需要特殊处理
    
    def on_step_end(self, args, state, control, **kwargs):
        """step结束回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        pass  # 不需要特殊处理
    
    def on_evaluate(self, args, state, control, **kwargs):
        """评估开始回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        self._logger.info("开始模型评估...")
    
    def on_save(self, args, state, control, **kwargs):
        """保存模型回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        self._logger.info("保存模型检查点...")
    
    def on_pre_optimizer_step(self, args, state, control, **kwargs):
        """优化器步骤前回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        pass  # 不需要特殊处理
    
    def on_optimizer_step(self, args, state, control, **kwargs):
        """优化器步骤回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        pass  # 不需要特殊处理
    
    def on_prediction_step(self, args, state, control, **kwargs):
        """预测步骤回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        pass  # 不需要特殊处理
    
    def on_predict(self, args, state, control, **kwargs):
        """预测开始回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        pass  # 不需要特殊处理
    
    def on_train_end(self, args, state, control, **kwargs):
        """训练结束回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
        """
        self._logger.info("训练完成！")
    
    def on_log(self, args, state, control, logs=None, **kwargs):
        """训练日志回调。
        
        Args:
            args: 训练参数。
            state: 训练状态。
            control: 训练控制。
            logs: 日志字典。
        """
        if logs:
            if "loss" in logs:
                self._logger.info(f"Step {state.global_step}: Loss = {logs['loss']:.4f}")
            if "eval_loss" in logs:
                self._logger.info(f"Eval: Loss = {logs['eval_loss']:.4f}, F1 = {logs.get('eval_f1', 0):.4f}")
                
                # 早停检查
                current_f1 = logs.get('eval_f1', 0)
                if current_f1 > self._best_f1:
                    self._best_f1 = current_f1
                    self._no_improve_count = 0
                    self._logger.info(f"✓ 新的最佳F1分数: {self._best_f1:.4f}")
                else:
                    self._no_improve_count += 1
                    self._logger.info(f"  F1未提升 ({self._no_improve_count}/{self._patience})")
                    
                if self._no_improve_count >= self._patience:
                    self._logger.info(f"触发早停机制！F1分数连续{self._patience}轮未提升")
                    control.should_training_stop = True


class ChinesePhishingDataset(Dataset):
    """中文钓鱼邮件数据集类。

    用于BERT模型训练的数据集包装器。
    """

    def __init__(
        self,
        texts: list[str],
        labels: list[int],
        tokenizer: DistilBertTokenizer,
        max_length: int = 512,
    ):
        """初始化数据集。

        Args:
            texts: 邮件文本列表。
            labels: 标签列表（0=正常，1=钓鱼）。
            tokenizer: BERT分词器。
            max_length: 最大序列长度。
        """
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        """返回数据集大小。"""
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """获取单个样本。

        Args:
            idx: 样本索引。

        Returns:
            包含input_ids, attention_mask, labels的字典。
        """
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            return_token_type_ids=False,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(label, dtype=torch.long),
        }

    def __del__(self):
        """清理内存。"""
        del self.texts
        del self.labels
        del self.tokenizer


class BERTTrainingConfig:
    """BERT模型训练配置。"""

    def __init__(
        self,
        dataset_path: Path,
        model_path: Path,
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
        max_length: int = 512,
        test_size: float = 0.2,
        random_state: int = 42,
        model_name: str = "bert-base-chinese",
    ):
        self.dataset_path = dataset_path
        self.model_path = model_path
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.max_length = max_length
        self.test_size = test_size
        self.random_state = random_state
        self.model_name = model_name


class BERTPhishingTrainer:
    """基于BERT的钓鱼邮件模型训练器。

    使用bert-base-chinese预训练模型进行微调，专门用于中文钓鱼邮件检测。
    """

    def __init__(
        self,
        config: BERTTrainingConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """初始化训练器。

        Args:
            config: 训练配置。
            logger: 日志记录器。
        """
        self._config = config
        self._logger = logger or logging.getLogger(__name__)

        self._tokenizer = None
        self._model = None

    def train(self) -> Dict[str, float]:
        """训练BERT模型。

        Returns:
            训练指标字典。
        """
        self._logger.info("=" * 60)
        self._logger.info("开始BERT钓鱼邮件模型训练")
        self._logger.info("=" * 60)

        self._logger.info(f"数据集路径: {self._config.dataset_path}")
        self._logger.info(f"模型保存路径: {self._config.model_path}")
        self._logger.info(f"预训练模型: {self._config.model_name}")
        self._logger.info(f"训练轮数: {self._config.epochs}")
        self._logger.info(f"批次大小: {self._config.batch_size}")
        self._logger.info(f"学习率: {self._config.learning_rate}")

        try:
            # 加载数据集
            self._load_dataset()
            self._prepare_data()
            
            # 训练模型并获取结果
            result = self._train_model()
            
            # 保存模型
            self._save_model()

            self._logger.info("=" * 60)
            self._logger.info("训练完成！")
            if result and 'metrics' in result:
                metrics = result['metrics']
                self._logger.info(f"准确率: {metrics['accuracy']:.4f}")
                self._logger.info(f"精确率: {metrics['precision']:.4f}")
                self._logger.info(f"召回率: {metrics['recall']:.4f}")
                self._logger.info(f"F1分数: {metrics['f1_score']:.4f}")
            self._logger.info("=" * 60)

            return result

        except Exception as e:
            self._logger.error(f"训练失败: {e}", exc_info=True)
            raise

    def _load_dataset(self) -> None:
        """加载和预处理数据集。"""
        self._logger.info("加载数据集...")

        try:
            df = pd.read_csv(self._config.dataset_path)
            self._logger.info(f"数据集大小: {len(df)} 条")

            # 数据清洗和预处理
            df = self._preprocess_data(df)
            
            # 不再限制数据集大小，使用所有可用数据

            # 数据清洗
            df = df.dropna(subset=['text', 'target'])
            df = df[df['text'].str.len() > 10]
            
            self._df = df

            self._logger.info("数据集统计:")
            self._logger.info(f"  正常邮件: {len(df[df['target'] == 0])}")
            self._logger.info(f"  钓鱼邮件: {len(df[df['target'] == 1])}")
            
        except Exception as e:
            self._logger.error(f"加载数据集失败: {e}", exc_info=True)
            raise

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据预处理。"""
        # 先合并邮件内容创建text列
        if "subject" in df.columns and "content" in df.columns:
            df["text"] = df["subject"].fillna("") + " " + df["content"].fillna("")
        elif "text" not in df.columns:
            raise ValueError("数据集必须包含 text 列或 subject + content 列")
        
        # 去除重复数据
        df = df.drop_duplicates(subset=['text'], keep='first').copy()
        
        # 文本清洗
        df['text'] = df['text'].apply(self._clean_text)
        
        # 平衡数据集（如果样本不均衡）
        normal_count = len(df[df['target'] == 0])
        phishing_count = len(df[df['target'] == 1])
        
        if abs(normal_count - phishing_count) > min(normal_count, phishing_count) * 0.3:
            self._logger.info("数据集不均衡，进行平衡处理...")
            df = self._balance_dataset(df)
        
        return df

    def _clean_text(self, text: str) -> str:
        """文本清洗。"""
        if not isinstance(text, str):
            return ""
        
        # 去除多余的空格和换行
        text = ' '.join(text.split())
        
        # 只去除明显的控制字符，保留大部分内容
        import re
        # 只移除控制字符和不可见字符
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()

    def _balance_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """平衡数据集。"""
        from sklearn.utils import resample
        
        df_normal = df[df['target'] == 0]
        df_phishing = df[df['target'] == 1]
        
        if len(df_normal) > len(df_phishing):
            df_phishing = resample(df_phishing, 
                                 replace=True, 
                                 n_samples=len(df_normal), 
                                 random_state=42)
        else:
            df_normal = resample(df_normal, 
                               replace=True, 
                               n_samples=len(df_phishing), 
                               random_state=42)
        
        return pd.concat([df_normal, df_phishing]).sample(frac=1, random_state=42)

    def _stratified_sample(self, df: pd.DataFrame, max_samples: int = 2000) -> pd.DataFrame:
        """分层采样。"""
        from sklearn.model_selection import train_test_split
        
        # 确保每个类别都有足够的样本
        min_samples_per_class = max_samples // 4
        
        df_normal = df[df['target'] == 0]
        df_phishing = df[df['target'] == 1]
        
        # 对每个类别进行采样
        if len(df_normal) > min_samples_per_class:
            df_normal = df_normal.sample(n=min_samples_per_class, random_state=42)
        
        if len(df_phishing) > min_samples_per_class:
            df_phishing = df_phishing.sample(n=min_samples_per_class, random_state=42)
        
        # 合并并打乱
        df_sampled = pd.concat([df_normal, df_phishing])
        df_sampled = df_sampled.sample(frac=1, random_state=42).reset_index(drop=True)
        
        return df_sampled

    def _prepare_data(self) -> None:
        """准备训练和验证数据。"""
        self._logger.info("准备训练数据...")

        from sklearn.model_selection import train_test_split

        # 不再限制数据集大小，使用所有可用数据

        X_train, X_val, y_train, y_val = train_test_split(
            self._df["text"].tolist(),
            self._df["target"].tolist(),
            test_size=0.2,  # 减少验证集比例
            random_state=self._config.random_state,
            stratify=self._df["target"].tolist(),
        )

        self._logger.info(f"训练集大小: {len(X_train)}")
        self._logger.info(f"验证集大小: {len(X_val)}")

        # 总是从预训练模型开始，确保tokenizer和模型匹配
        self._logger.info(f"从Hugging Face加载预训练模型和tokenizer: {self._config.model_name}")
        self._tokenizer = DistilBertTokenizer.from_pretrained(self._config.model_name)
        self._model = DistilBertForSequenceClassification.from_pretrained(
            self._config.model_name,
            num_labels=2,
            output_attentions=False,
            output_hidden_states=False,
        )
        
        # 设置设备
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(device)
        self._logger.info(f"使用设备: {device}")

        self._train_dataset = ChinesePhishingDataset(
            X_train, y_train, self._tokenizer, self._config.max_length
        )
        self._val_dataset = ChinesePhishingDataset(
            X_val, y_val, self._tokenizer, self._config.max_length
        )

    def _train_model(self) -> None:
        """训练模型。"""
        self._logger.info("开始训练...")

        # 训练参数优化（CPU环境优化）
        training_args = TrainingArguments(
            output_dir=str(self._config.model_path.parent),
            num_train_epochs=self._config.epochs,  # 使用配置中的训练轮数
            per_device_train_batch_size=self._config.batch_size,  # 使用配置中的批次大小
            per_device_eval_batch_size=self._config.batch_size,
            warmup_steps=50,  # 增加warmup步数
            weight_decay=0.01,
            logging_dir=str(self._config.model_path.parent / "logs"),
            logging_steps=10,
            eval_strategy="epoch",  # 每个epoch评估一次
            eval_steps=10,
            save_strategy="epoch",  # 每个epoch保存一次模型
            load_best_model_at_end=True,  # 加载最佳模型
            learning_rate=self._config.learning_rate,  # 使用配置中的学习率
            fp16=False,  # 禁用混合精度（CPU环境下反而慢）
            dataloader_num_workers=0,
            remove_unused_columns=True,
            report_to="none",
            save_total_limit=2,  # 保存最后2个checkpoint
            gradient_accumulation_steps=1,  # 禁用梯度累积
            metric_for_best_model="eval_f1",  # 使用F1分数作为最佳模型指标
            greater_is_better=True,  # 指标越大越好
        )

        from sklearn.metrics import (
            accuracy_score,
            precision_recall_fscore_support,
        )

        def compute_metrics(eval_pred):
            logits, labels = eval_pred
            predictions = logits.argmax(axis=-1)
            precision, recall, f1, _ = precision_recall_fscore_support(
                labels, predictions, average="binary"
            )
            acc = accuracy_score(labels, predictions)
            return {
                "accuracy": acc,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }

        self._trainer = Trainer(
            model=self._model,
            args=training_args,
            train_dataset=self._train_dataset,
            eval_dataset=self._val_dataset,
            compute_metrics=compute_metrics,
        )

        self._logger.info("开始训练模型...")
        self._trainer.train()
        self._logger.info("模型训练完成！")
        
        # 在清理数据集之前先进行评估和可视化生成
        metrics = self._evaluate_model()
        self._current_metrics = metrics  # 保存当前指标
        
        # 在删除验证集之前生成需要验证集的可视化图表
        self._logger.info("生成可视化图表...")
        visualizations = self.generate_visualizations()
        
        # 清理训练数据集内存
        del self._train_dataset
        del self._val_dataset
        
        # 清理模型内存
        import gc
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        # 保存训练历史数据
        self._save_training_history()
        
        return {
            "metrics": metrics,
            "visualizations": visualizations,
            "model_path": str(self._config.model_path)
        }

    def _evaluate_model(self) -> Dict[str, float]:
        """评估模型。"""
        self._logger.info("评估模型...")

        import torch
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support

        # 对验证集进行预测
        predictions = []
        labels = []

        for i in range(len(self._val_dataset)):
            item = self._val_dataset[i]
            input_ids = item["input_ids"].unsqueeze(0)
            attention_mask = item["attention_mask"].unsqueeze(0)
            label = item["labels"]

            with torch.no_grad():
                outputs = self._model(input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                pred = torch.argmax(logits, dim=1).item()

            predictions.append(pred)
            labels.append(label.item())

        # 计算性能指标
        precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average="binary")
        accuracy = accuracy_score(labels, predictions)

        metrics = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
        }

        return metrics

    def _save_model(self) -> None:
        """保存模型。"""
        self._logger.info("保存模型...")

        self._config.model_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存训练后的模型和tokenizer
        self._trainer.model.save_pretrained(str(self._config.model_path))
        self._tokenizer.save_pretrained(str(self._config.model_path))

        # 保存训练指标
        metrics_path = self._config.model_path / "training_metrics.json"
        
        # 从训练结果中获取指标
        metrics = getattr(self, '_current_metrics', {})
        
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "model_name": self._config.model_name,
                    "epochs": self._config.epochs,
                    "batch_size": self._config.batch_size,
                    "learning_rate": self._config.learning_rate,
                    "max_length": self._config.max_length,
                    "dataset_path": str(self._config.dataset_path),
                    "accuracy": float(metrics.get("accuracy", 0.0)),
                    "precision": float(metrics.get("precision", 0.0)),
                    "recall": float(metrics.get("recall", 0.0)),
                    "f1_score": float(metrics.get("f1_score", 0.0)),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        self._logger.info(f"模型已保存到: {self._config.model_path}")

    def _save_training_history(self) -> None:
        """保存训练历史数据到CSV文件。"""
        try:
            # 保存到static目录
            static_dir = Path(__file__).parent.parent.parent.parent / "static"
            static_dir.mkdir(parents=True, exist_ok=True)
            
            history_path = static_dir / "training_history.csv"
            
            # 使用字典来合并同一step的训练和验证数据
            history_data = {}
            
            # 从训练日志中提取数据
            if hasattr(self._trainer.state, 'log_history'):
                for log in self._trainer.state.log_history:
                    if 'loss' in log or 'eval_loss' in log:
                        epoch = log.get('epoch', 0)
                        step = log.get('step', 0)
                        
                        # 使用step作为唯一键
                        key = step
                        
                        if key not in history_data:
                            history_data[key] = {
                                'epoch': epoch,
                                'step': step,
                                'train_loss': None,
                                'eval_loss': None,
                                'train_accuracy': None,
                                'eval_accuracy': None
                            }
                        
                        # 填充对应的字段
                        if 'loss' in log:
                            history_data[key]['train_loss'] = log['loss']
                        if 'eval_loss' in log:
                            history_data[key]['eval_loss'] = log['eval_loss']
                        if 'eval_accuracy' in log:
                            history_data[key]['eval_accuracy'] = log['eval_accuracy']
            
            if history_data:
                df = pd.DataFrame(list(history_data.values()))
                df.to_csv(history_path, index=False)
                self._logger.info(f"训练历史已保存到: {history_path}")
            else:
                self._logger.warning("没有训练历史数据可保存")
                
        except Exception as e:
            self._logger.error(f"保存训练历史失败: {e}", exc_info=True)

    def generate_visualizations(self) -> Dict[str, str]:
        """生成训练可视化图表。

        Returns:
            包含base64编码图片的字典。
        """
        self._logger.info("生成可视化图表...")

        visualizations = {}
        
        # 保存到static目录
        static_dir = Path(__file__).parent.parent.parent.parent / "static"
        viz_dir = static_dir / "visualizations"
        viz_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. 训练损失曲线
            loss_chart = self._plot_loss_curve()
            if loss_chart:
                visualizations["loss"] = loss_chart
                self._save_visualization(loss_chart, viz_dir / "loss_curve.png")

            # 2. 训练准确率曲线
            accuracy_chart = self._plot_accuracy_curve()
            if accuracy_chart:
                visualizations["accuracy"] = accuracy_chart
                self._save_visualization(accuracy_chart, viz_dir / "accuracy_curve.png")

            # 3. 性能指标柱状图
            metrics_chart = self._plot_metrics_bar()
            if metrics_chart:
                visualizations["metrics_bar"] = metrics_chart
                self._save_visualization(metrics_chart, viz_dir / "metrics_bar.png")

            # 4. 混淆矩阵（需要验证集预测）
            confusion_chart = self._plot_confusion_matrix()
            if confusion_chart:
                visualizations["confusion"] = confusion_chart
                self._save_visualization(confusion_chart, viz_dir / "confusion_matrix.png")

            # 5. ROC曲线（需要验证集预测）
            roc_chart = self._plot_roc_curve()
            if roc_chart:
                visualizations["roc"] = roc_chart
                self._save_visualization(roc_chart, viz_dir / "roc_curve.png")

            # 6. PR曲线（需要验证集预测）
            pr_chart = self._plot_pr_curve()
            if pr_chart:
                visualizations["pr"] = pr_chart
                self._save_visualization(pr_chart, viz_dir / "pr_curve.png")

            self._logger.info(f"可视化图表生成完成，共生成 {len(visualizations)} 个图表")
            self._logger.info(f"图表已保存到: {viz_dir}")
            return visualizations

        except Exception as e:
            self._logger.error(f"生成可视化图表失败: {e}", exc_info=True)
            return visualizations

    def _save_visualization(self, base64_image: str, file_path: Path) -> None:
        """保存base64编码的图片到文件。

        Args:
            base64_image: base64编码的图片字符串。
            file_path: 保存路径。
        """
        import base64

        try:
            image_data = base64.b64decode(base64_image)
            with open(file_path, "wb") as f:
                f.write(image_data)
            self._logger.info(f"图表已保存: {file_path}")
        except Exception as e:
            self._logger.error(f"保存图表失败 {file_path}: {e}")

    def _plot_loss_curve(self) -> str:
        """绘制训练损失曲线。"""
        if not hasattr(self, "_trainer") or not self._trainer.state.log_history:
            return ""

        train_losses = []
        train_epochs = []
        eval_losses = []
        eval_epochs = []
        
        for log in self._trainer.state.log_history:
            if "loss" in log:
                train_losses.append(log["loss"])
                train_epochs.append(log.get("epoch", len(train_losses)))
            elif "eval_loss" in log:
                eval_losses.append(log["eval_loss"])
                eval_epochs.append(log.get("epoch", len(eval_losses)))

        if not train_losses and not eval_losses:
            return ""

        fig, ax = plt.subplots(figsize=(10, 6))
        
        if train_losses:
            ax.plot(train_epochs, train_losses, label="训练损失", color="#e74c3c", linewidth=2)
        if eval_losses:
            ax.plot(eval_epochs, eval_losses, label="验证损失", color="#3498db", linewidth=2)
        
        ax.set_xlabel("训练轮次 (Epoch)", fontsize=12)
        ax.set_ylabel("损失 (Loss)", fontsize=12)
        ax.set_title("模型训练过程中的损失变化", fontsize=14, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        return self._fig_to_base64(fig)

    def _plot_accuracy_curve(self) -> str:
        """绘制训练准确率曲线。"""
        if not hasattr(self, "_trainer") or not self._trainer.state.log_history:
            return ""

        train_accuracies = []
        eval_accuracies = []
        epochs = []
        
        for log in self._trainer.state.log_history:
            if "eval_accuracy" in log:
                eval_accuracies.append(log["eval_accuracy"])
                epochs.append(log.get("epoch", len(eval_accuracies)))

        if not eval_accuracies:
            return ""

        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(epochs, eval_accuracies, label="验证准确率", color="#3498db", linewidth=2)
        ax.set_xlabel("训练轮次 (Epoch)", fontsize=12)
        ax.set_ylabel("准确率 (Accuracy)", fontsize=12)
        ax.set_title("模型训练过程中的准确率变化", fontsize=14, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        return self._fig_to_base64(fig)

    def _plot_roc_curve(self) -> str:
        """绘制ROC曲线。"""
        # 检查验证集是否存在
        if not hasattr(self, "_val_dataset") or self._val_dataset is None:
            self._logger.warning("验证集不存在，无法绘制ROC曲线")
            return ""

        fig, ax = plt.subplots(figsize=(10, 6))

        try:
            import torch
            from sklearn.metrics import roc_curve, auc

            # 对验证集进行预测
            probs = []
            labels = []

            for i in range(len(self._val_dataset)):
                item = self._val_dataset[i]
                input_ids = item["input_ids"].unsqueeze(0)
                attention_mask = item["attention_mask"].unsqueeze(0)
                label = item["labels"]

                with torch.no_grad():
                    outputs = self._model(input_ids, attention_mask=attention_mask)
                    logit = outputs.logits
                    prob = torch.softmax(logit, dim=1)[:, 1].item()

                probs.append(prob)
                labels.append(label.item())

            # 计算ROC曲线
            fpr, tpr, _ = roc_curve(labels, probs)
            roc_auc = auc(fpr, tpr)
            
            # 保存ROC数据到static目录
            static_dir = Path(__file__).parent.parent.parent.parent / "static"
            roc_path = static_dir / "roc_data.npz"
            np.savez(roc_path, fpr=fpr, tpr=tpr, auc=roc_auc)
            self._logger.info(f"ROC数据已保存到: {roc_path}")

            ax.plot(fpr, tpr, color="#e74c3c", linewidth=2, label=f"ROC曲线 (AUC = {roc_auc:.2f})")
            ax.plot([0, 1], [0, 1], color="#7f8c8d", linestyle="--", linewidth=2, label="随机分类器")
            ax.set_xlabel("假正例率 (False Positive Rate)", fontsize=12)
            ax.set_ylabel("真正例率 (True Positive Rate)", fontsize=12)
            ax.set_title("接收者操作特征曲线 (ROC)", fontsize=14, fontweight="bold")
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)

        except Exception as e:
            self._logger.error(f"绘制ROC曲线失败: {e}")
            return self._fig_to_base64(fig)

        return self._fig_to_base64(fig)

    def _plot_pr_curve(self) -> str:
        """绘制PR曲线。"""
        # 检查验证集是否存在
        if not hasattr(self, "_val_dataset") or self._val_dataset is None:
            self._logger.warning("验证集不存在，无法绘制PR曲线")
            return ""

        fig, ax = plt.subplots(figsize=(10, 6))

        try:
            import torch
            from sklearn.metrics import precision_recall_curve, average_precision_score

            # 对验证集进行预测
            probs = []
            labels = []

            for i in range(len(self._val_dataset)):
                item = self._val_dataset[i]
                input_ids = item["input_ids"].unsqueeze(0)
                attention_mask = item["attention_mask"].unsqueeze(0)
                label = item["labels"]

                with torch.no_grad():
                    outputs = self._model(input_ids, attention_mask=attention_mask)
                    logit = outputs.logits
                    prob = torch.softmax(logit, dim=1)[:, 1].item()

                probs.append(prob)
                labels.append(label.item())

            # 计算PR曲线
            precision, recall, _ = precision_recall_curve(labels, probs)
            avg_precision = average_precision_score(labels, probs)
            
            # 保存PR数据到static目录
            static_dir = Path(__file__).parent.parent.parent.parent / "static"
            pr_path = static_dir / "pr_data.npz"
            np.savez(pr_path, precision=precision, recall=recall, ap=avg_precision)
            self._logger.info(f"PR数据已保存到: {pr_path}")

            ax.plot(recall, precision, color="#3498db", linewidth=2, label=f"PR曲线 (AP = {avg_precision:.2f})")
            ax.set_xlabel("召回率 (Recall)", fontsize=12)
            ax.set_ylabel("精确率 (Precision)", fontsize=12)
            ax.set_title("精确率-召回率曲线", fontsize=14, fontweight="bold")
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)

        except Exception as e:
            self._logger.error(f"绘制PR曲线失败: {e}")
            return self._fig_to_base64(fig)

        return self._fig_to_base64(fig)

    def _plot_confusion_matrix(self) -> str:
        """绘制混淆矩阵。"""
        # 检查验证集是否存在
        if not hasattr(self, "_val_dataset") or self._val_dataset is None:
            self._logger.warning("验证集不存在，无法绘制混淆矩阵")
            return ""

        fig, ax = plt.subplots(figsize=(8, 6))

        try:
            import torch
            from sklearn.metrics import confusion_matrix
            import numpy as np
            
            # 定义static目录
            static_dir = Path(__file__).parent.parent.parent.parent / "static"

            # 对验证集进行预测
            predictions = []
            labels = []

            for i in range(len(self._val_dataset)):
                item = self._val_dataset[i]
                input_ids = item["input_ids"].unsqueeze(0)
                attention_mask = item["attention_mask"].unsqueeze(0)
                label = item["labels"]

                with torch.no_grad():
                    outputs = self._model(input_ids, attention_mask=attention_mask)
                    logits = outputs.logits
                    pred = torch.argmax(logits, dim=1).item()

                predictions.append(pred)
                labels.append(label.item())

            # 计算混淆矩阵
            cm = confusion_matrix(labels, predictions)
            
            # 保存混淆矩阵数据到static目录
            cm_path = static_dir / "confusion_matrix.npy"
            np.save(cm_path, cm)
            self._logger.info(f"混淆矩阵数据已保存到: {cm_path}")

            # 绘制热力图
            sns.heatmap(
                cm,
                annot=True,
                fmt="d",
                cmap="Blues",
                ax=ax,
                cbar_kws={"label": "Count"},
            )
            ax.set_xlabel("预测标签", fontsize=12)
            ax.set_ylabel("真实标签", fontsize=12)
            ax.set_title("混淆矩阵", fontsize=14, fontweight="bold")
            ax.set_xticklabels(["正常邮件", "钓鱼邮件"])
            ax.set_yticklabels(["正常邮件", "钓鱼邮件"])

        except Exception as e:
            self._logger.error(f"绘制混淆矩阵失败: {e}")
            return self._fig_to_base64(fig)

        return self._fig_to_base64(fig)

    def _plot_metrics_bar(self) -> str:
        """绘制性能指标柱状图。"""
        fig, ax = plt.subplots(figsize=(10, 6))

        if hasattr(self, "_current_metrics"):
            metrics = self._current_metrics
            metric_names = ["准确率", "精确率", "召回率", "F1分数"]
            metric_values = [
                metrics.get("accuracy", 0.0),
                metrics.get("precision", 0.0),
                metrics.get("recall", 0.0),
                metrics.get("f1_score", 0.0),
            ]

            colors = ["#3498db", "#e74c3c", "#f39c12", "#2ecc71"]
            bars = ax.bar(metric_names, metric_values, color=colors, alpha=0.8, edgecolor="black", linewidth=1.5)

            # 在柱子上显示数值
            for bar, value in zip(bars, metric_values):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{value:.4f}",
                    ha="center",
                    va="bottom",
                    fontsize=11,
                    fontweight="bold",
                )

            ax.set_ylabel("分数", fontsize=12)
            ax.set_title("模型性能指标", fontsize=14, fontweight="bold")
            ax.set_ylim(0, 1.0)
            ax.grid(True, alpha=0.3, axis="y")

        return self._fig_to_base64(fig)

    def _fig_to_base64(self, fig) -> str:
        """将matplotlib图形转换为base64编码的PNG。

        Args:
            fig: matplotlib图形对象。

        Returns:
            base64编码的PNG图片字符串。
        """
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return img_str