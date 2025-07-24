import logging
import configparser
from telethon import TelegramClient
from telethon.tl.types import Message, PeerUser, PeerChannel, PeerChat
from telethon.errors.rpcerrorlist import ChatForwardsRestrictedError

# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# 从配置文件读取日志等级，默认为WARNING
log_level_str = config.get('logging', 'level', fallback='WARNING')
log_level = getattr(logging, log_level_str.upper(), logging.WARNING)

# 配置日志
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def process_message(client: TelegramClient, message: Message, target_group: int):
    """
    消息处理的主函数，未来可以扩展以调用更多处理模块。
    目前只负责转发消息。
    """
    await _forward_message(client, message, target_group)

async def _forward_message(client: TelegramClient, message: Message, target_group: int):
    """
    将消息转发到目标群组，并处理不允许转发的异常情况。
    """
    # 获取真实的发送人ID
    sender = await message.get_sender()
    if sender:
        sender_id = sender.id
    else:
        sender_id = "未知"
    
    # 获取真实的聊天ID
    chat_id = message.chat_id
    
    try:
        await client.forward_messages(target_group, message)
        logger.info(f"消息 {message.id} (来自用户 {sender_id}, 群组 {chat_id}) 已成功转发至 {target_group}")
    except ChatForwardsRestrictedError:
        logger.warning(f"无法转发消息 {message.id} (来自用户 {sender_id}, 群组 {chat_id})，来源对话禁止转发。")
    except Exception as e:
        logger.error(f"转发消息 {message.id} (来自用户 {sender_id}, 群组 {chat_id}) 时发生未知错误: {e}") 