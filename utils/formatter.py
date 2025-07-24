import pytz
from telethon.tl.types import Message
from typing import Optional

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

async def format_message(event: "Message") -> Optional[str]:
    """
    格式化 Telethon 消息事件为可读字符串。

    如果消息是纯媒体内容，则使用'[图片]'等占位符。
    如果消息没有文本和可识别的媒体，则返回 None。
    
    格式包含：时间、群组/私聊名称、发送者信息、内容。
    支持处理私聊、群组消息和回复。

    :param event: Telethon 的消息事件对象。
    :return: 格式化后的字符串，或 None。
    """
    message_content = event.text.strip() if event.text else ""

    # 如果没有文本，检查是否为媒体消息，并设置占位符
    if not message_content:
        placeholder = None
        if event.photo:
            placeholder = "[图片]"
        elif event.sticker:
            placeholder = "[表情]"
        elif event.video:

            placeholder = "[视频]"
        elif event.document:
            placeholder = "[文件]"
        
        if placeholder:
            message_content = placeholder
        else:
            # 如果既没有文本，也没有可识别的媒体，则不处理此消息
            return None

    # 时间转换：UTC → 北京时间
    beijing_time = event.date.astimezone(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

    # 获取 sender 信息
    sender = await event.get_sender()
    username = 'Unknown'
    nickname = 'Unknown'
    if sender:
        username = f"@{sender.username}" if sender.username else "NoUsername"
        first = getattr(sender, 'first_name', '') or ''
        last = getattr(sender, 'last_name', '') or ''
        nickname = (first + ' ' + last).strip() or 'Unknown'

    sender_id = getattr(sender, 'id', 'Unknown ID')

    # 获取 chat 信息
    chat = await event.get_chat()
    chat_title = getattr(chat, 'title', None) or 'Direct Message'
    chat_id = event.chat_id

    # 回复消息提示
    reply_hint = ''
    if event.is_reply:
        reply_hint = "↪ 回复了某条消息\\n"

    # 消息内容
    # message_content = event.text.strip()

    # 最终格式
    return f"[{beijing_time}] [{chat_title}({chat_id})][{username}-{nickname}({sender_id})]:\\n{reply_hint}{message_content}"
