import asyncio
from telethon import TelegramClient
from config import API_ID, API_HASH

# 初始化 Telegram 客户端
client = TelegramClient('session_name', API_ID, API_HASH)

# 消息转发队列
message_queue = asyncio.Queue() 