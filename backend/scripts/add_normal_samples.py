#!/usr/bin/env python3
"""
添加正常社交样本到数据集，解决关键词误判问题
"""

import pandas as pd
from pathlib import Path

def add_normal_social_samples(dataset_path: Path):
    """添加正常社交样本"""
    
    # 读取现有数据集
    df = pd.read_csv(dataset_path)
    
    # 添加正常社交样本（包含"上网"等容易误判的词汇）
    normal_samples = [
        # 社交邀请类
        "一起去上网吧，好久没见了",
        "周末一起上网打游戏怎么样？",
        "要不要一起去上网？我请客",
        "今天有空吗？一起上网聊天",
        "下班后一起上网放松一下",
        
        # 日常对话类
        "我经常上网查资料",
        "上网学习很有用",
        "最近上网时间有点多",
        "上网看电影很方便",
        "我每天都上网看新闻",
        
        # 工作相关类
        "明天上网开会",
        "上网查一下这个信息",
        "上网提交作业",
        "上网处理工作邮件",
        "上网参加在线培训",
        
        # 娱乐相关类
        "上网听音乐很棒",
        "上网玩游戏很过瘾",
        "上网购物很方便",
        "上网看电视剧",
        "上网刷短视频",
        
        # 其他正常用法
        "可以上网查一下路线",
        "我帮你上网查查",
        "上网搜索一下这个话题",
        "上网看看天气预报",
        "上网了解一下这个产品"
    ]
    
    # 为每个正常样本创建数据行
    new_rows = []
    for text in normal_samples:
        new_rows.append({
            'subject': '日常交流',
            'sender': f'normal{len(df) + len(new_rows)}@example.com',
            'content': text,
            'target': 0  # 正常邮件
        })
    
    # 添加到数据集
    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df, df_new], ignore_index=True)
    
    # 保存更新后的数据集
    df_combined.to_csv(dataset_path, index=False, encoding='utf-8')
    
    print(f"✅ 成功添加 {len(normal_samples)} 个正常社交样本")
    print(f"📊 数据集总样本数: {len(df_combined)}")
    print(f"📈 正常邮件数: {len(df_combined[df_combined['target'] == 0])}")
    print(f"📉 钓鱼邮件数: {len(df_combined[df_combined['target'] == 1])}")
    
    # 检查"上网"的分布
    shangwang_count = df_combined['content'].str.contains('上网', na=False).sum()
    normal_shangwang = df_combined[df_combined['target'] == 0]['content'].str.contains('上网', na=False).sum()
    phishing_shangwang = df_combined[df_combined['target'] == 1]['content'].str.contains('上网', na=False).sum()
    
    print(f"\n🔍 '上网'关键词分析:")
    print(f"   总出现次数: {shangwang_count}")
    print(f"   正常邮件中: {normal_shangwang}")
    print(f"   钓鱼邮件中: {phishing_shangwang}")
    print(f"   钓鱼占比: {phishing_shangwang/shangwang_count*100:.1f}%")

if __name__ == "__main__":
    dataset_path = Path("/home/master/my_first_project/Argus/backend/app/utils/phishing/datasets/chinese_phishing_dataset.csv")
    add_normal_social_samples(dataset_path)