import uvicorn
from app.db.init_db import init_all
import asyncio

async def main():
    # 初始化数据库和管理员账号
    await init_all()
    
    # 启动应用
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    # 运行初始化和启动服务器
    asyncio.run(main())