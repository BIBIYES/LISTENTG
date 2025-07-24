"""
ListenTG - Telegram 消息监听和转发工具
"""

import logging
from telethon import functions
from tg_client import client
from event_handlers import forwarder
from config import PHONE, FORWARDING_DELAY_SECONDS

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 主程序入口
def main():
    """
    主程序入口函数。
    
    初始化客户端，设置在线状态，并开始监听消息。
    """
    logger.info("正在启动客户端...")
    
    # 启动客户端
    client.start(PHONE)
    
    # 在事件循环中创建并启动转发器任务
    client.loop.create_task(forwarder())
    
    # 设置为在线状态，确保实时接收消息
    client(functions.account.UpdateStatusRequest(offline=False))
    
    logger.info("客户端已启动，正在监听新消息...")
    logger.info(f"消息将通过队列转发，速率控制为每 {FORWARDING_DELAY_SECONDS} 秒一条")
    
    # 开始运行客户端
    client.run_until_disconnected()

if __name__ == "__main__":
    main()