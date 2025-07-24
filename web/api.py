import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from handlers.database import db_manager, DashboardStats, MessageResult
from typing import List

logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="ListenTG Web UI")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# 配置 Jinja2 模板
templates = Jinja2Templates(directory="web/templates")

@app.on_event("startup")
async def startup_event():
    """应用启动时，连接数据库。"""
    await db_manager.connect()
    # 在应用启动时也初始化一次，确保表存在
    await db_manager.init_db()
    logger.info("Web API 启动，数据库已连接。")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时，断开数据库连接。"""
    await db_manager.close()
    logger.info("Web API 关闭，数据库连接已断开。")

# --- 页面路由 ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """返回数据看板的主页面。"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/search", response_class=HTMLResponse)
async def read_search(request: Request):
    """返回搜索页面。"""
    return templates.TemplateResponse("search.html", {"request": request})

# --- API 数据路由 ---

@app.get("/api/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """提供数据看板所需的统计数据。"""
    try:
        stats = await db_manager.get_stats_for_dashboard()
        return stats
    except Exception as e:
        logger.error(f"获取统计数据时出错: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"message": "获取统计数据失败"})

@app.get("/api/search", response_model=List[MessageResult])
async def search_messages_api(query: str):
    """根据查询词搜索消息。"""
    if not query or len(query) < 2:
        return []
    try:
        results = await db_manager.search_messages(query)
        return results
    except Exception as e:
        logger.error(f"搜索消息时出错: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"message": "搜索消息失败"}) 