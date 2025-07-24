import asyncio
from datetime import datetime, timedelta
import logging
import aiosqlite
from fastapi import APIRouter, HTTPException

# 调整时区，北京时间 = UTC+8
TIMEZONE_OFFSET = timedelta(hours=8)

# 创建API路由器
router = APIRouter()
logger = logging.getLogger(__name__)
DB_PATH = 'listentg_messages.db'

async def get_db_connection():
    """ 创建并返回一个数据库连接 """
    try:
        return await aiosqlite.connect(DB_PATH)
    except aiosqlite.Error as e:
        logger.error(f"无法连接到数据库: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

async def query_db(query: str, params: tuple = ()):
    """ 执行数据库查询并返回所有结果 """
    conn = await get_db_connection()
    try:
        conn.row_factory = aiosqlite.Row
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()
    except aiosqlite.Error as e:
        logger.error(f"数据库查询失败: {e} | Query: {query}")
        return []
    finally:
        await conn.close()
        
@router.get("/api/dashboard-data")
async def get_dashboard_data():
    """
    一个端点，聚合所有仪表盘所需的数据。
    """
    # 在单个响应中并行获取所有数据
    results = await asyncio.gather(
        get_top_chats_last_7_days(),
        get_total_messages_last_7_days(),
        get_top_users_last_7_days(),
        get_top_chats_today(),
        get_hourly_activity_last_30_days(),
        search_messages("") # 初始为空搜索
    )

    return {
        "top_chats_7_days": results[0],
        "total_messages_7_days": results[1],
        "top_users_7_days": results[2],
        "top_chats_today": results[3],
        "hourly_activity_30_days": results[4],
        "search_results": results[5]
    }

async def get_top_chats_last_7_days():
    """ 获取过去7天内消息最多的群组 """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    query = """
        SELECT chat_title, COUNT(*) as message_count
        FROM messages
        WHERE date >= ? AND chat_type IN ('Group', 'Channel')
        GROUP BY chat_title
        ORDER BY message_count DESC
        LIMIT 10;
    """
    return await query_db(query, (seven_days_ago,))

async def get_hourly_activity_last_30_days():
    """ 获取过去30天每小时的消息频率 (考虑北京时间) """
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    query = """
        SELECT
            STRFTIME('%Y-%m-%d', date) as day,
            STRFTIME('%H', date, '+8 hours') as hour,
            COUNT(*) as message_count
        FROM messages
        WHERE date >= ?
        GROUP BY day, hour;
    """
    return await query_db(query, (thirty_days_ago,))

async def get_total_messages_last_7_days():
    """ 获取过去7天每天的总消息数 """
    seven_days_ago = datetime.utcnow().date() - timedelta(days=7)
    query = """
        SELECT STRFTIME('%Y-%m-%d', date) as day, COUNT(*) as message_count
        FROM messages
        WHERE date >= ?
        GROUP BY day
        ORDER BY day;
    """
    return await query_db(query, (seven_days_ago,))
    
async def get_top_users_last_7_days():
    """ 获取过去7天内消息最多的用户 """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    query = """
        SELECT sender_name, COUNT(*) as message_count
        FROM messages
        WHERE sender_name IS NOT 'Unknown'
        AND date >= ?
        GROUP BY sender_name
        ORDER BY message_count DESC
        LIMIT 10;
    """
    return await query_db(query, (seven_days_ago,))

async def get_top_chats_today():
    """ 获取当天消息最多的群组 """
    today_start = datetime.utcnow().date()
    query = """
        SELECT chat_title, COUNT(*) as message_count
        FROM messages
        WHERE date >= ? AND chat_type IN ('Group', 'Channel')
        GROUP BY chat_title
        ORDER BY message_count DESC
        LIMIT 10;
    """
    return await query_db(query, (today_start,))

@router.get("/api/search")
async def search_messages_endpoint(q: str = ""):
    """ 根据关键词模糊搜索消息 """
    return await search_messages(q)

async def search_messages(query: str):
    """ 实际执行消息搜索的函数 """
    if not query:
        return []
    
    search_query = """
        SELECT chat_title, sender_name, text, date
        FROM messages
        WHERE text LIKE ?
        ORDER BY date DESC
        LIMIT 20;
    """
    return await query_db(search_query, (f'%{query}%',)) 