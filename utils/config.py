import configparser
import logging
from typing import Set, Optional

# 获取日志记录器
logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """自定义配置错误异常"""
    pass

class Config:
    """
    负责加载和管理来自 config.ini 的配置。
    """
    def __init__(self, path: str = 'config.ini'):
        """
        初始化并加载配置。

        :param path: config.ini 文件的路径。
        :raises ConfigError: 当配置文件未找到、格式错误或缺少必要选项时。
        """
        self.config = configparser.ConfigParser()
        if not self.config.read(path, encoding='utf-8'):
            raise ConfigError(f"配置文件 '{path}' 未找到。")
        
        self._load_settings()

    def _load_settings(self):
        """从加载的配置中解析各个设置项。"""
        try:
            # --- Telegram 凭据 ---
            self.api_id: int = self.config.getint('telegram', 'api_id')
            self.api_hash: str = self.config.get('telegram', 'api_hash')
            self.phone: str = self.config.get('telegram', 'phone')

            # --- 转发设置 ---
            self.target_group: int = self.config.getint('forwarding', 'target_group')
            self.forwarding_delay_seconds: float = self.config.getfloat('forwarding', 'forwarding_delay_seconds', fallback=2.0)

            # --- 日志设置 ---
            self.log_level: str = self.config.get('logging', 'level', fallback='INFO').upper()

            # --- 过滤器设置 ---
            exclude_chat_ids_str = self.config.get('filters', 'exclude_chat_ids', fallback='')
            self.exclude_chat_ids: Set[int] = {int(id.strip()) for id in exclude_chat_ids_str.split(',') if id.strip()}

            exclude_sender_ids_str = self.config.get('filters', 'exclude_sender_ids', fallback='')
            self.exclude_sender_ids: Set[int] = {int(id.strip()) for id in exclude_sender_ids_str.split(',') if id.strip()}

        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise ConfigError(f"配置文件格式错误: {e}")
        except ValueError as e:
            raise ConfigError(f"配置文件中的值无效: {e}")

# 创建一个全局可用的配置实例
try:
    settings = Config()
except ConfigError as e:
    logger.error(e)
    # 在无法加载配置时，可以决定是退出还是使用默认值
    # 这里我们选择退出，但在大型应用中可能有更复杂的处理
    exit(1) 