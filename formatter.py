import pytz

import pytz
from html import escape

async def format_message(event):
    """
    格式化 Telethon 消息事件为可读字符串。
    包含：时间、群组名、发送者、内容，支持处理私聊、群聊和回复消息。
    """
    if not event.text:
        return None

    # 时间转换：UTC → 北京时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = event.date.astimezone(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    # 获取 sender 信息
    sender = await event.get_sender()
    username = 'Unknown'
    # 昵称
    nickname = 'Unknown'
    if sender:
        username = f"@{sender.username}"
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
        reply_hint = "↪ 回复了某条消息\n"

    # 消息内容
    message_content = event.text.strip()

    # 可选：escape HTML 字符，防止出错
    # message_content = escape(message_content)

    # 最终格式
    return f"[{beijing_time}] [{chat_title}({chat_id})][{username}-{nickname}({sender_id})]:\n{reply_hint}{message_content}"
