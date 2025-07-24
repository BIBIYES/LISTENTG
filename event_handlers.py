import logging
import asyncio
from telethon import events
from formatter import format_message
from tg_client import client, message_queue
from config import EXCLUDE_CHAT_IDS, EXCLUDE_SENDER_IDS, TARGET_GROUP, FORWARDING_DELAY_SECONDS

logger = logging.getLogger(__name__)

@client.on(events.NewMessage)
async def handler(event):
    """
    处理新消息事件的回调函数。
    """
    chat = await event.message.get_chat()
    chat_id = chat.id if chat else event.chat_id
    
    sender = await event.message.get_sender()
    sender_id = sender.id if sender else event.sender_id
    
    if chat_id in EXCLUDE_CHAT_IDS:
        logger.info(f"消息来自被排除的群组 {chat_id}，已忽略。")
        return
    if sender_id in EXCLUDE_SENDER_IDS:
        logger.info(f"消息来自被排除的用户 {sender_id}，已忽略。")
        return

    formatted_message = await format_message(event.message)
    if formatted_message:
        logger.info(formatted_message)

    await message_queue.put(event)
    logger.info(f"消息已加入转发队列。当前队列剩余: {message_queue.qsize()}")

    try:
        # 获取聊天实体信息
        entity = await client.get_entity(event.chat_id)
        # 根据不同类型处理
        if hasattr(entity, 'megagroup') and entity.megagroup:
            # 超级组
            await client.send_read_acknowledge(
                event.chat_id,
                max_id=0,  # 0表示所有消息
                clear_mentions=True,
                clear_reactions=True
            )
        else:
            # 普通群组或私聊
            await client.send_read_acknowledge(
                event.chat_id,
                max_id=event.message.id,
                clear_mentions=True
            )
            
    except Exception as e:
        print(f"标记已读失败: {e}")
async def forwarder():
    """
    从队列中取出消息并以固定速率转发。
    """
    while True:
        event = await message_queue.get()
        try:
            await event.forward_to(TARGET_GROUP)
            q_size = message_queue.qsize()
            logger.info(f"消息已转发。队列剩余: {q_size}")
        except Exception as e:
            logger.error(f"转发消息时出错: {e}")
        finally:
            message_queue.task_done()
        
        await asyncio.sleep(FORWARDING_DELAY_SECONDS) 