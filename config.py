import configparser
import logging

logger = logging.getLogger(__name__)

# 加载配置文件
config = configparser.ConfigParser()
try:
    config.read('config.ini', encoding='utf-8')

    # --- 从配置文件加载设置 ---
    # 凭据设置
    API_ID = config.getint('telegram', 'api_id')
    API_HASH = config.get('telegram', 'api_hash')
    PHONE = config.get('telegram', 'phone')

    # 转发目标
    TARGET_GROUP = int(config.get('forwarding', 'target_group'))
    FORWARDING_DELAY_SECONDS = config.getfloat('forwarding', 'forwarding_delay_seconds', fallback=2.0)

    # 过滤器设置
    exclude_chat_ids_str = config.get('filters', 'exclude_chat_ids', fallback='')
    EXCLUDE_CHAT_IDS = {int(id.strip()) for id in exclude_chat_ids_str.split(',') if id.strip()}

    exclude_sender_ids_str = config.get('filters', 'exclude_sender_ids', fallback='')
    EXCLUDE_SENDER_IDS = {int(id.strip()) for id in exclude_sender_ids_str.split(',') if id.strip()}

except FileNotFoundError:
    logger.error("配置文件 'config.ini' 未找到。请确保它与脚本在同一目录下。")
    exit()
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    logger.error(f"配置文件 'config.ini' 格式错误: {e}")
    exit()
except ValueError as e:
    logger.error(f"配置文件中的值无效: {e}")
    exit() 