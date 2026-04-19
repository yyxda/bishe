"""创建小规模中文钓鱼邮件数据集（10条：5钓鱼+5正常）。"""

import pandas as pd
from pathlib import Path

# 数据集路径
dataset_path = Path(__file__).parent / "chinese_phishing_dataset.csv"

# 5个钓鱼邮件
phishing_emails = [
    {
        "subject": "【重要】您的订单需要确认",
        "sender": "order-confirm@payment-service.com",
        "content": """尊敬的客户：

您有一笔订单需要确认，请点击以下链接查看详情：

http://payment-service.com/order/confirm

订单金额：9999元
订单编号：2024398398
如未操作，请忽略此邮件。

客服中心""",
        "target": 1
    },
    {
        "subject": "免费领取VIP会员，限时优惠",
        "sender": "vip-promo@identity-check.com",
        "content": """亲爱的用户：

限时免费领取VIP会员，价值1999元！
点击以下链接立即领取：
http://identity-check.com/free-claim

活动时间有限，先到先得！

祝您使用愉快！""",
        "target": 1
    },
    {
        "subject": "【紧急】您的银行卡存在风险",
        "sender": "bank-risk@security-center.com",
        "content": """尊敬的客户：

系统检测到您的银行卡存在异常交易风险，请立即点击以下链接进行验证：

http://security-center.com/card/verify

如不及时验证，您的银行卡将被冻结。

银行安全中心""",
        "target": 1
    },
    {
        "subject": "恭喜您中奖10000元！限时领取",
        "sender": "lucky-draw@promo-reward.com",
        "content": """亲爱的用户：

恭喜您被系统随机抽中，获得10000元现金奖励！

请点击以下链接领取您的奖励：
http://promo-reward.com/claim

活动时间有限，请尽快领取！

祝您好运！""",
        "target": 1
    },
    {
        "subject": "您的密码即将过期，请及时修改",
        "sender": "system@account-update.com",
        "content": """尊敬的用户：

您的账户密码即将过期，为了保障您的账户安全，请立即点击以下链接修改密码：

http://account-update.com/password/change

如不及时修改，您的账户将无法正常使用。

系统管理员""",
        "target": 1
    }
]

# 5个正常邮件
normal_emails = [
    {
        "subject": "关于2024年春季学期课程安排的通知",
        "sender": "jwc@hhstu.edu.cn",
        "content": """各位同学：

根据学校教学安排，现将2024年春季学期课程安排通知如下：

1. 课程时间：2024年3月1日至2024年7月15日
2. 课程地点：各教学楼
3. 注意事项：请按时上课，不得无故缺课

如有疑问，请联系教务处。

教务处
2024年2月20日""",
        "target": 0
    },
    {
        "subject": "关于校园网维护的通知",
        "sender": "network@hhstu.edu.cn",
        "content": """各位师生：

为了提供更好的网络服务，学校将于2024年3月15日进行校园网维护，届时网络将暂时中断。

维护时间：02:00-06:00

给您带来的不便，敬请谅解。

网络中心""",
        "target": 0
    },
    {
        "subject": "图书馆开放时间调整通知",
        "sender": "library@hhstu.edu.cn",
        "content": """各位读者：

根据学校安排，图书馆开放时间调整如下：

周一至周五：08:00-22:00
周六至周日：09:00-21:00

特此通知。

图书馆
2024年3月1日""",
        "target": 0
    },
    {
        "subject": "Re: 关于下周的小组讨论",
        "sender": "student1@qq.com",
        "content": """你好！

关于下周的小组讨论，我建议在周三下午3点进行，地点在图书馆三楼会议室。

你觉得这个时间可以吗？

祝好！""",
        "target": 0
    },
    {
        "subject": "附件：2024年工作计划",
        "sender": "manager@company.com",
        "content": """您好！

附件是2024年的工作计划，请查收。

如有任何问题，请随时联系我。

祝好！""",
        "target": 0
    }
]

# 合并数据集
all_emails = phishing_emails + normal_emails

# 创建DataFrame
df = pd.DataFrame(all_emails)

# 保存数据集
df.to_csv(dataset_path, index=False)

print(f"数据集已创建: {dataset_path}")
print(f"钓鱼邮件: {len(df[df['target']==1])}")
print(f"正常邮件: {len(df[df['target']==0])}")
print(f"总计: {len(df)}")