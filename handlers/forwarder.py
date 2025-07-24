import asyncio
import logging
from tg_client import client_manager
from utils.config import settings

logger = logging.getLogger(__name__)

# 从 client_manager 获取消息队列
message_queue = client_manager.get_queue()

async def forwarder_task():
    """
    一个独立的后台任务，持续从队列中获取消息并转发。
    
    - 以配置中指定的速率进行转发。
    - 记录成功和失败的转发操作。
    """
    logger.info(f"消息转发器已启动，将以每 {settings.forwarding_delay_seconds} 秒一次的速率转发。")
    while True:
        try:
            event = await message_queue.get()
            
            await event.forward_to(settings.target_group)
            
            q_size = message_queue.qsize()
            logger.info(f"一条消息已成功转发至 {settings.target_group}。队列剩余: {q_size}")
            
        except Exception as e:
            logger.error(f"转发消息时发生严重错误: {e}", exc_info=True)
            # 即使转发失败，也继续处理下一条，避免阻塞
            
        finally:
            message_queue.task_done()
            # 遵循配置的延迟，控制转发速率
            await asyncio.sleep(settings.forwarding_delay_seconds) 