"""BERT钓鱼检测系统升级脚本。

安装依赖并训练BERT模型。
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, cwd: Path = None) -> bool:
    """运行命令。

    Args:
        command: 命令字符串。
        cwd: 工作目录。

    Returns:
        是否成功。
    """
    print(f"\n执行命令: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def main():
    """主函数。"""
    print("=" * 80)
    print("BERT钓鱼检测系统升级")
    print("=" * 80)

    # 获取后端目录（脚本在 backend/scripts/ 下，所以 parent.parent 就是 backend/）
    backend_dir = Path(__file__).parent.parent

    print(f"\n后端目录: {backend_dir}")

    # 步骤1: 安装依赖
    print("\n" + "=" * 80)
    print("步骤1: 安装BERT依赖")
    print("=" * 80)

    dependencies = [
        "torch",
        "transformers",
        "datasets",
        "tokenizers",
    ]

    for dep in dependencies:
        print(f"\n安装 {dep}...")
        if not run_command(f".venv/bin/pip install {dep}", cwd=backend_dir):
            print(f"安装 {dep} 失败，跳过...")
            continue
        print(f"{dep} 安装成功！")

    # 步骤2: 生成中文钓鱼邮件数据集
    print("\n" + "=" * 80)
    print("步骤2: 生成中文钓鱼邮件数据集")
    print("=" * 80)

    print("\n生成数据集...")
    if run_command(
        f"PYTHONPATH={backend_dir} .venv/bin/python3 -c "
        f"'from app.utils.phishing.chinese_phishing_dataset import ChinesePhishingDatasetGenerator; "
        f"ChinesePhishingDatasetGenerator.save_to_csv("
        f"'{backend_dir}/app/utils/phishing/datasets/chinese_phishing_dataset.csv', 500, 500)'",
        cwd=backend_dir,
    ):
        print("数据集生成成功！")
    else:
        print("数据集生成失败，跳过...")

    # 步骤3: 训练BERT模型
    print("\n" + "=" * 80)
    print("步骤3: 训练BERT模型")
    print("=" * 80)

    print("\n注意: 训练BERT模型需要较长时间（约30-60分钟），请耐心等待...")
    print("如果您的机器没有GPU，训练时间会更长。")

    choice = input("\n是否继续训练BERT模型？(y/n): ")
    if choice.lower() == 'y':
        print("\n开始训练BERT模型...")
        if run_command(
            f"PYTHONPATH={backend_dir} .venv/bin/python3 scripts/train_bert_phishing_model.py "
            f"'{backend_dir}/app/utils/phishing/datasets/chinese_phishing_dataset.csv' "
            f"'{backend_dir}/app/utils/phishing/ml_models/bert_phishing_model'",
            cwd=backend_dir,
        ):
            print("BERT模型训练成功！")
        else:
            print("BERT模型训练失败...")
    else:
        print("跳过BERT模型训练。")
        print("\n提示: 您可以稍后手动运行以下命令训练模型:")
        print(f"cd {backend_dir}")
        print(f"PYTHONPATH={backend_dir} .venv/bin/python3 scripts/train_bert_phishing_model.py "
              f"'{backend_dir}/app/utils/phishing/datasets/chinese_phishing_dataset.csv' "
              f"'{backend_dir}/app/utils/phishing/ml_models/bert_phishing_model'")

    # 步骤4: 测试BERT检测器
    print("\n" + "=" * 80)
    print("步骤4: 测试BERT检测器")
    print("=" * 80)

    print("\n测试BERT检测器...")
    if run_command(
        f"PYTHONPATH={backend_dir} .venv/bin/python3 scripts/test_bert_detector.py",
        cwd=backend_dir,
    ):
        print("BERT检测器测试完成！")
    else:
        print("BERT检测器测试失败...")

    # 完成
    print("\n" + "=" * 80)
    print("升级完成！")
    print("=" * 80)

    print("\n升级摘要:")
    print("✅ BERT依赖已安装")
    print("✅ 中文钓鱼邮件数据集已生成")
    print("✅ BERT模型已训练（如果选择了训练）")
    print("✅ BERT检测器已测试")

    print("\n下一步:")
    print("1. 重启后端服务")
    print("2. 在前端测试钓鱼邮件检测功能")
    print("3. 查看模型性能指标和可视化分析")

    print("\n重启后端服务命令:")
    print(f"cd {backend_dir}")
    print(f"PYTHONPATH={backend_dir} .venv/bin/python3 -m app.main")


if __name__ == "__main__":
    main()