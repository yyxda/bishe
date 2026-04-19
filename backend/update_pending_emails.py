"""批量更新所有 PENDING 状态的邮件为 COMPLETED"""

import asyncio
from app.core.container import Container
from app.entities.email_entity import EmailEntity, PhishingStatus
from sqlalchemy import update

async def update_pending_emails():
    """批量更新所有 PENDING 状态的邮件为 COMPLETED"""
    container = Container()
    await container.initialize()
    
    try:
        # 查询所有 PENDING 状态的邮件数量
        count_query = "SELECT COUNT(*) FROM email_messages WHERE phishing_status = 'PENDING'"
        result = await container.db_manager.session.execute(count_query)
        count = result.scalar()
        
        print(f"找到 {count} 封 PENDING 状态的邮件")
        
        if count > 0:
            # 批量更新所有 PENDING 状态的邮件为 COMPLETED
            update_query = update(EmailEntity).where(
                EmailEntity.phishing_status == PhishingStatus.PENDING
            ).values(phishing_status=PhishingStatus.COMPLETED)
            
            result = await container.db_manager.session.execute(update_query)
            await container.db_manager.session.commit()
            
            print(f"成功更新 {result.rowcount} 封邮件的状态为 COMPLETED")
        else:
            print("没有需要更新的邮件")
            
    except Exception as e:
        print(f"更新失败: {e}")
        await container.db_manager.session.rollback()
    finally:
        await container.close()

if __name__ == "__main__":
    asyncio.run(update_pending_emails())