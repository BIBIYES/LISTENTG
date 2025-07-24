import asyncio
from datetime import datetime
import pytz

async def format_message(event):
    """
    Formats a Telethon message event into a readable string.
    """
    if not event.text:
        return None

    # Time conversion to Beijing time
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = event.date.astimezone(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    # Sender name
    sender = await event.get_sender()
    sender_name = getattr(sender, 'first_name', 'Unknown')
    if hasattr(sender, 'last_name') and sender.last_name:
        sender_name += f" {sender.last_name}"

    # Chat title (if any)
    chat = await event.get_chat()
    chat_title = getattr(chat, 'title', 'Direct Message') if hasattr(chat, 'title') else "Direct Message"


    # Message content
    message_content = event.text

    return f"[{beijing_time}] [{chat_title}] {sender_name}: {message_content}" 