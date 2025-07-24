import logging
import sys
from utils.config import settings

def setup_logging():
    """
    配置全局日志记录。
    
    - 设置日志级别。
    - 定义日志格式。
    - 将日志输出到控制台。
    """
    log_level = getattr(logging, settings.log_level, logging.INFO)
    
    # 创建一个格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建一个处理器，用于输出到控制台
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    
    # 获取根日志记录器并添加处理器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除任何可能存在的旧处理器，避免日志重复输出
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(stream_handler)
    
    logging.info(f"日志系统已配置，级别为: {settings.log_level}") 