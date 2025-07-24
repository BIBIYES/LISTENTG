import configparser
from telethon.sync import TelegramClient
from telethon import events
from formatter import format_message

config = configparser.ConfigParser()
config.read('config.ini')

api_id = config.getint('telegram', 'api_id')
api_hash = config.get('telegram', 'api_hash')
phone = config.get('telegram', 'phone')

client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    # 监听所有新消息并打印
    formatted_message = await format_message(event.message)
    if formatted_message:
        print(formatted_message)

client.start(phone)
print("客户端已启动，正在监听新消息...")
client.run_until_disconnected()
