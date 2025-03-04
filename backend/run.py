import uvicorn
from app.db.init_db import init_all
import asyncio
import os


async def main():
    # 初始化数据库和管理员账号
    await init_all()

    # 启动应用
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # 允许外部访问
        port=8000,
        reload=False,  # 生产环境关闭热重载
    )


if __name__ == "__main__":
    # 运行初始化和启动服务器
    asyncio.run(main())
