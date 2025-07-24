"""
ListenTG - Telegram 消息监听和转发工具

这个脚本监听指定 Telegram 账号接收的所有消息，
并根据配置将消息转发到目标群组或频道。
支持消息过滤、格式化显示和日志记录。
"""


import configparser
from telethon.sync import TelegramClient
from telethon import events, functions
from formatter import format_message



# 加载配置文件
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# --- 从配置文件加载设置 ---
# 凭据设置
api_id = config.getint('telegram', 'api_id')
api_hash = config.get('telegram', 'api_hash')
phone = config.get('telegram', 'phone')

# 转发目标 - 确保读取整数ID，包括负数
# 使用int()而不是getint()以支持负数ID（如 -1001234567890）
target_group = int(config.get('forwarding', 'target_group'))  

# 过滤器设置
exclude_chat_ids_str = config.get('filters', 'exclude_chat_ids', fallback='')
exclude_sender_ids_str = config.get('filters', 'exclude_sender_ids', fallback='')

# 将字符串ID列表转换为整数集合以便快速查找
exclude_chat_ids = {int(id.strip()) for id in exclude_chat_ids_str.split(',') if id.strip()}
exclude_sender_ids = {int(id.strip()) for id in exclude_sender_ids_str.split(',') if id.strip()}

# 初始化 Telegram 客户端
client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    """
    处理新消息事件的回调函数。
    
    当客户端收到新消息时，此函数会被调用。它负责：
    1. 检查消息是否应该被过滤（来自被排除的群组或用户）
    2. 格式化并打印消息内容
    3. 将消息转发到目标群组
    4. 标记消息为已读
    
    Args:
        event (events.NewMessage.Event): 新消息事件对象
    """
    # 获取完整的内部聊天ID
    chat = await event.message.get_chat()
    chat_id = chat.id if chat else event.chat_id
    
    # 获取完整的内部发送人ID
    sender = await event.message.get_sender()
    sender_id = sender.id if sender else event.sender_id
    
    # 检查是否需要排除（过滤）
    if chat_id in exclude_chat_ids:
        print(f"消息来自被排除的群组 {chat_id}，已忽略。")
        return
    if sender_id in exclude_sender_ids:
        print(f"消息来自被排除的用户 {sender_id}，已忽略。")
        return

    # 格式化并打印消息
    formatted_message = await format_message(event.message)
    if formatted_message:
        print(formatted_message)

    # 转发消息
    await event.forward_to(target_group)
    
    # 标记消息为已读
    try:
        await client.send_read_acknowledge(event.chat_id, event.message)
    except Exception as e:
        print(f"标记消息已读时出错: {e}")


# 主程序入口
def main():
    """
    主程序入口函数。
    
    初始化客户端，设置在线状态，并开始监听消息。
    """
    # 启动客户端
    client.start(phone)
    
    # 设置为在线状态，确保实时接收消息
    client(functions.account.UpdateStatusRequest(offline=False))
    
    print("客户端已启动，正在监听新消息...")
    
    # 开始运行客户端
    client.run_until_disconnected()

if __name__ == "__main__":
    main()