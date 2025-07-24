import logging
from telethon import events
from tg_client import client_manager
from utils.config import settings
from utils.formatter import format_message
from handlers.database import db_manager

logger = logging.getLogger(__name__)

# 从 client_manager 获取客户端实例
client = client_manager.get_client()
message_queue = client_manager.get_queue()

@client.on(events.NewMessage())
async def new_message_handler(event: events.NewMessage.Event):
    """
    处理新消息事件。

    - 标记消息为已读。
    - 根据配置过滤来自特定群组或发送者的消息。
    - 将消息存入数据库。
    - 格式化消息用于日志记录。
    - 将通过过滤的消息放入转发队列。
    """
    try:
        # 第一步：执行原有的逻辑
        await event.mark_read()
        
        chat = await event.get_chat()
        chat_id = getattr(chat, 'id', event.chat_id)
        
        sender = await event.get_sender()
        sender_id = getattr(sender, 'id', event.sender_id)
        
        if chat_id in settings.exclude_chat_ids:
            logger.info(f"消息来自被排除的群组 {chat_id}，已忽略。")
            return
        if sender_id in settings.exclude_sender_ids:
            logger.info(f"消息来自被排除的用户 {sender_id}，已忽略。")
            return
        # 第二步：将消息存入数据库
        await db_manager.save_message(event)
        formatted_message = await format_message(event.message)
        if formatted_message:
            logger.info(formatted_message)

        await message_queue.put(event)
        logger.info(f"消息已加入转发队列。当前队列大小: {message_queue.qsize()}")

    except Exception as e:
        logger.error(f"处理新消息时发生错误: {e}", exc_info=True) 