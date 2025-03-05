import uvicorn
from app.db.init_db import init_all
import asyncio
import os
import signal
import logging
from uvicorn.config import Config
from uvicorn.server import Server


# 配置日志
logging.basicConfig(level=logging.WARNING)
# 禁用 uvicorn 的错误日志
logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
# 禁用 SQLAlchemy 的日志
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


async def main():
    print("\n" + "=" * 50)
    print("正在初始化数据库...")
    # 初始化数据库和管理员账号
    await init_all()

    # 使用 uvicorn API 方式启动服务器
    port = 8000
    host = "0.0.0.0"

    print("\n" + "=" * 50)
    print(f"✨ 服务器启动成功! ✨")
    print(f"🚀 API 服务运行于: http://{host}:{port}")
    print(f"📚 API 文档地址: http://{host}:{port}/docs")
    print(f"🔍 另一种文档: http://{host}:{port}/redoc")
    print("=" * 50 + "\n")

    config = Config(
        app="app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="warning",  # 降低日志级别
    )
    server = Server(config=config)

    # 设置信号处理
    should_exit = asyncio.Event()

    def signal_handler():
        print("\n正在优雅地关闭服务器...")
        should_exit.set()

    # 添加信号处理器
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # 创建服务器任务但不立即等待它
    server_task = asyncio.create_task(server.serve())

    # 等待关闭信号或服务器任务完成
    done, pending = await asyncio.wait(
        [server_task, asyncio.create_task(should_exit.wait())],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # 如果是因为信号而退出
    if should_exit.is_set():
        # 正确关闭服务器
        if hasattr(server, "should_exit"):
            server.should_exit = True

        # 等待服务器完成关闭过程
        try:
            await asyncio.wait_for(server_task, timeout=5.0)
            print("服务器已成功关闭")
        except asyncio.TimeoutError:
            print("服务器关闭超时，强制终止")
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
        except asyncio.CancelledError:
            print("服务器已成功关闭")


if __name__ == "__main__":
    try:
        # 运行初始化和启动服务器
        asyncio.run(main())
    except KeyboardInterrupt:
        # 这里不需要额外的提示，因为信号处理器已经提供了关闭信息
        pass
    except Exception as e:
        print(f"程序异常退出: {e}")
