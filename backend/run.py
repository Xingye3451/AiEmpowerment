import uvicorn
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

    # 导入必要的模块
    from app.db.init_db import ensure_db_exists, init_db, create_admin
    from app.db.init_social_accounts import init_social_account_tables

    # 按照正确的顺序初始化
    # 1. 确保数据库文件存在
    ensure_db_exists()

    # 2. 初始化数据库表结构
    await init_db()

    # 3. 创建管理员账号
    await create_admin()

    # 4. 初始化社交账号相关表
    await init_social_account_tables()

    print("数据库初始化完成！")

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
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
    except NotImplementedError:
        # Windows环境下可能不支持add_signal_handler
        import sys

        if sys.platform == "win32":
            print("Windows环境下使用替代信号处理方式")
            # 在Windows下使用替代方案
            import threading

            def win_signal_handler():
                import time

                while not should_exit.is_set():
                    try:
                        time.sleep(0.1)
                    except KeyboardInterrupt:
                        signal_handler()
                        break

            threading.Thread(target=win_signal_handler, daemon=True).start()

    # 创建服务器任务但不立即等待它
    server_task = asyncio.create_task(server.serve())

    # 等待关闭信号或服务器任务完成
    try:
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
    except Exception as e:
        print(f"服务器运行过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        # 确保服务器任务被取消
        if not server_task.done():
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    try:
        # 运行初始化和启动服务器
        asyncio.run(main())
    except KeyboardInterrupt:
        # 这里不需要额外的提示，因为信号处理器已经提供了关闭信息
        pass
    except Exception as e:
        import traceback

        print(f"程序异常退出: {e}")
        print("详细错误信息:")
        traceback.print_exc()
