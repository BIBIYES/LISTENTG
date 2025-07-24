
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from web.api import data as api_data

# 创建 FastAPI 应用实例
app = FastAPI(
    title="ListenTG WebUI",
    description="一个用于 ListenTG 的 Web 数据仪表盘。",
    version="0.1.0"
)

# 包含 API 路由器
app.include_router(api_data.router)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# 定义根路由，返回主页
@app.get("/")
async def read_index():
    """
    提供 Web 界面的主 HTML 文件。
    """
    return FileResponse('web/templates/index.html')

# 模块的其余部分将定义API端点
# ...

if __name__ == "__main__":
    # 使用 uvicorn 运行 FastAPI 应用
    # 这主要用于本地开发和测试
    uvicorn.run(app, host="0.0.0.0", port=8000) 