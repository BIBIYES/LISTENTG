"""
ListenTG - Telegram 消息监听和转发工具
"""

import asyncio
import logging
import multiprocessing
import uvicorn

from tg_client import client_manager
from utils.logger import setup_logging
from handlers.database import db_manager

# 导入事件处理器模块，确保 @client.on 装饰器被执行和注册
from handlers import message_handler
from handlers.forwarder import forwarder_task

# 在所有其他模块之前优先配置日志
setup_logging()
logger = logging.getLogger(__name__)

def run_web_server():
    """ 在一个单独的进程中运行 FastAPI Web 服务器 """
    from web.main import app  # 延迟导入以避免循环依赖问题
    logger.info("正在启动 Web 服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    """
    应用程序主入口。
    
    - 初始化数据库。
    - 初始化并启动客户端。
    - 在事件循环中创建并运行转发器任务。
    - 保持客户端持续运行。
    - 最后关闭数据库连接。
    """
    try:
        # 初始化数据库（连接并创建表）
        await db_manager.init_db()

        # 在一个独立的进程中启动 Web 服务器
        web_process = multiprocessing.Process(target=run_web_server)
        web_process.start()

        # 启动客户端（包含登录和设置在线状态）
        await client_manager.start()

        # 获取客户端的事件循环，并创建转发任务
        loop = client_manager.get_client().loop
        loop.create_task(forwarder_task())
        
        logger.info("系统已准备就绪，开始监听消息...")
        
        # 运行客户端直到断开连接
        await client_manager.run_until_disconnected()

    except Exception as e:
        logger.critical(f"应用主程序遇到无法恢复的错误，即将退出: {e}", exc_info=True)
    finally:
        logger.info("应用程序正在关闭...")
        
        # 确保 Web 服务器进程被终止
        if 'web_process' in locals() and web_process.is_alive():
            web_process.terminate()
            web_process.join()
            logger.info("Web 服务器已关闭。")

        await db_manager.close()
        logger.info("数据库连接已关闭。")

if __name__ == "__main__":
    # 确保多进程在 Windows 和其他平台上安全启动
    multiprocessing.freeze_support()
    asyncio.run(main())