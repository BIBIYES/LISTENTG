"""
ListenTG - Telegram 消息监听和转发工具
"""

import asyncio
import logging
import uvicorn
from tg_client import client_manager
from utils.logger import setup_logging
from web.api import app as web_app

# 导入事件处理器模块，确保 @client.on 装饰器被执行和注册
from handlers import message_handler
from handlers.forwarder import forwarder_task

# 在所有其他模块之前优先配置日志
setup_logging()
logger = logging.getLogger(__name__)

async def run_client():
    """启动 Telethon 客户端，并启动转发器任务。"""
    await client_manager.start()
    logger.info("Telethon 客户端已启动。")

    # 客户端启动后，在它的事件循环上创建转发任务
    client_manager.get_client().loop.create_task(forwarder_task())

    # 保持客户端运行
    await client_manager.run_until_disconnected()

async def main():
    """
    应用程序主入口。
    
    并行运行 Telethon 客户端和 FastAPI Web 服务器。
    """
    # 配置 Uvicorn 服务器
    config = uvicorn.Config(web_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    try:
        logger.info("正在启动 Web 服务器和 Telethon 客户端...")
    
        # 并行运行服务器和客户端
        await asyncio.gather(
            server.serve(),
            run_client()
        )

    except (KeyboardInterrupt, SystemExit):
        logger.info("收到关闭信号...")
    except Exception as e:
        logger.critical(f"应用主程序遇到无法恢复的错误: {e}", exc_info=True)
    finally:
        logger.info("应用程序正在关闭...")

if __name__ == "__main__":
    asyncio.run(main())