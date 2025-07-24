import aiosqlite
import logging
from telethon import events
from telethon.tl.types import User, Chat, Channel
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DB_PATH = 'listentg_messages.db'

# Pydantic 模型，用于定义API返回的数据结构
class DailyStat(BaseModel):
    date: str
    count: int

class GroupStat(BaseModel):
    chat_title: str
    count: int

class TopTalker(BaseModel):
    sender_name: str
    count: int

class DashboardStats(BaseModel):
    today_message_count: int
    seven_day_group_stats: List[GroupStat]
    seven_day_total_stats: List[DailyStat]
    seven_day_top_talker: Optional[TopTalker]

class MessageResult(BaseModel):
    chat_title: str
    sender_name: str
    text: str
    date: datetime


class DatabaseManager:
    """
    管理 SQLite 数据库的连接和操作。
    使用 aiosqlite 实现异步数据库访问。
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """建立数据库连接。"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            logger.info(f"已成功连接到数据库: {self.db_path}")

    async def close(self):
        """关闭数据库连接。"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("数据库连接已关闭。")

    async def init_db(self):
        """
        初始化数据库，创建 `messages` 表（如果不存在）。
        """
        if not self._connection:
            await self.connect()
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            chat_type TEXT,
            chat_title TEXT,
            sender_id INTEGER,
            sender_name TEXT,
            sender_username TEXT,
            text TEXT,
            raw_text TEXT,
            date TIMESTAMP NOT NULL,
            is_reply BOOLEAN,
            reply_to_message_id INTEGER
        );
        """
        await self._connection.execute(create_table_sql)
        await self._connection.commit()
        logger.info("数据库表 'messages' 已初始化。")

    async def get_stats_for_dashboard(self) -> DashboardStats:
        """获取仪表板所需的所有统计数据。"""
        if not self._connection:
            raise ConnectionError("数据库未连接。")

        async with self._connection.execute("PRAGMA foreign_keys = ON") as cursor: # 只是为了确保连接活跃
            pass

        # 1. 今日所有消息数量
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        async with self._connection.execute(
            "SELECT COUNT(*) FROM messages WHERE date >= ?", (today_start,)
        ) as cursor:
            today_count = (await cursor.fetchone())[0]

        # 2. 7日群聊消息排行榜
        seven_days_ago = datetime.now() - timedelta(days=7)
        group_stats_query = """
            SELECT chat_title, COUNT(*) as msg_count
            FROM messages
            WHERE date >= ? AND chat_type IN ('Group', 'Channel')
            GROUP BY chat_title
            ORDER BY msg_count DESC
            LIMIT 10;
        """
        async with self._connection.execute(group_stats_query, (seven_days_ago,)) as cursor:
            group_stats_rows = await cursor.fetchall()
            group_stats = [GroupStat(chat_title=row[0], count=row[1]) for row in group_stats_rows]

        # 3. 7日所有消息数量折线图
        total_stats_query = """
            SELECT DATE(date) as day, COUNT(*) as msg_count
            FROM messages
            WHERE date >= ?
            GROUP BY day
            ORDER BY day;
        """
        async with self._connection.execute(total_stats_query, (seven_days_ago,)) as cursor:
            total_stats_rows = await cursor.fetchall()
            total_stats = [DailyStat(date=row[0], count=row[1]) for row in total_stats_rows]

        # 4. 7日发言量最高的人
        top_talker_query = """
            SELECT sender_name, COUNT(*) as msg_count
            FROM messages
            WHERE date >= ? AND sender_name IS NOT 'Unknown'
            GROUP BY sender_name
            ORDER BY msg_count DESC
            LIMIT 1;
        """
        top_talker = None
        async with self._connection.execute(top_talker_query, (seven_days_ago,)) as cursor:
            top_talker_row = await cursor.fetchone()
            if top_talker_row:
                top_talker = TopTalker(sender_name=top_talker_row[0], count=top_talker_row[1])

        return DashboardStats(
            today_message_count=today_count,
            seven_day_group_stats=group_stats,
            seven_day_total_stats=total_stats,
            seven_day_top_talker=top_talker,
        )

    async def search_messages(self, query: str) -> List[MessageResult]:
        """根据内容搜索消息。"""
        if not self._connection:
            raise ConnectionError("数据库未连接。")
        
        search_query = """
            SELECT chat_title, sender_name, text, date
            FROM messages
            WHERE text LIKE ?
            ORDER BY date DESC
            LIMIT 50;
        """
        async with self._connection.execute(search_query, (f'%{query}%',)) as cursor:
            rows = await cursor.fetchall()
            return [MessageResult(chat_title=row[0], sender_name=row[1], text=row[2], date=row[3]) for row in rows]

    async def save_message(self, event: events.NewMessage.Event):
        """
        从事件对象中提取信息并存入数据库。
        对于媒体消息，会使用'[图片]'等占位符作为内容。
        """
        if not self._connection:
            logger.error("数据库未连接，无法保存消息。")
            return
        
        message = event.message

        # -- 提取和处理消息内容 --
        text_content = message.text
        raw_text_content = message.raw_text

        # 如果没有文本，检查是否为媒体消息，并设置占位符
        if not text_content:
            placeholder = None
            if message.photo:
                placeholder = "[图片]"
            elif message.sticker:
                placeholder = "[表情]"
            elif message.video:
                placeholder = "[视频]"
            elif message.document:
                placeholder = "[文件]"
            
            if placeholder:
                text_content = placeholder
                raw_text_content = placeholder
        # -- 内容处理结束 --
        
        # 提取会话信息
        chat = await message.get_chat()
        chat_type = None
        if isinstance(chat, User):
            chat_type = 'User'
        elif isinstance(chat, Chat):
            chat_type = 'Group'
        elif isinstance(chat, Channel):
            chat_type = 'Channel'
            
        # 提取发送者信息
        sender = await message.get_sender()
        sender_name = "Unknown"
        sender_username = "Unknown"
        if sender:
            first = getattr(sender, 'first_name', '') or ''
            last = getattr(sender, 'last_name', '') or ''
            sender_name = (first + ' ' + last).strip() or 'Unknown'
            sender_username = getattr(sender, 'username', 'NoUsername')

        insert_sql = """
        INSERT INTO messages (
            message_id, chat_id, chat_type, chat_title, sender_id, sender_name,
            sender_username, text, raw_text, date, is_reply, reply_to_message_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            message.id,
            message.chat_id,
            chat_type,
            getattr(chat, 'title', 'Direct Message'),
            getattr(sender, 'id', None),
            sender_name,
            sender_username,
            text_content,
            raw_text_content,
            message.date,
            message.is_reply,
            message.reply_to_msg_id
        )

        try:
            await self._connection.execute(insert_sql, params)
            await self._connection.commit()
            logger.info(f"消息 (ID: {message.id}) 已成功存入数据库。")
        except Exception as e:
            logger.error(f"向数据库插入消息时出错: {e}", exc_info=True)

# 创建一个全局的数据库管理器实例
db_manager = DatabaseManager()
