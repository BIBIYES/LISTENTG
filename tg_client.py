import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
from utils.config import settings

logger = logging.getLogger(__name__)

class ClientManager:
    """
    管理 Telegram 客户端和消息队列。
    """
    def __init__(self):
        """
        初始化客户端管理器。
        """
        self.client = TelegramClient(
            'autotg_session', 
            settings.api_id, 
            settings.api_hash
        )
        self.message_queue = asyncio.Queue()
        logger.info("客户端管理器已初始化。")

    async def start(self):
        """
        启动 Telegram 客户端并设置为在线状态。
        """
        logger.info("正在启动客户端...")
        await self.client.start(phone=settings.phone)
        await self.client(UpdateStatusRequest(offline=False))
        logger.info("客户端已启动并设置为在线状态。")

    def get_client(self) -> TelegramClient:
        """
        获取 TelegramClient 实例。
        """
        return self.client

    def get_queue(self) -> asyncio.Queue:
        """
        获取消息队列实例。
        """
        return self.message_queue

    async def run_until_disconnected(self):
        """
        运行客户端直到断开连接。
        """
        await self.client.run_until_disconnected()

# 创建一个全局的客户端管理器实例
client_manager = ClientManager() 