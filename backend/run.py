import uvicorn
import asyncio
import os
import signal
import logging
import sys
import atexit
import threading
import time
from uvicorn.config import Config
from uvicorn.server import Server


# 配置日志
logging.basicConfig(level=logging.WARNING)
# 禁用 uvicorn 的错误日志
logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
# 禁用 SQLAlchemy 的日志
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# 全局变量，用于跟踪服务器状态
server_should_exit = False
force_exit_timer = None


# 强制退出函数
def force_exit():
    print("\n服务器关闭超时，强制退出...")
    os._exit(0)  # 使用os._exit强制退出，不执行清理操作


# 在Windows环境下设置控制台处理程序
if sys.platform == "win32":
    try:
        import ctypes

        # 定义Windows API常量
        CTRL_C_EVENT = 0
        CTRL_BREAK_EVENT = 1

        # 定义控制台处理函数
        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)
        def console_ctrl_handler(event):
            global server_should_exit, force_exit_timer
            if event in (CTRL_C_EVENT, CTRL_BREAK_EVENT):
                if not server_should_exit:
                    print("\n检测到Ctrl+C，正在优雅地关闭服务器...")
                    server_should_exit = True

                    # 设置强制退出计时器
                    if force_exit_timer is None:
                        force_exit_timer = threading.Timer(5.0, force_exit)
                        force_exit_timer.daemon = True
                        force_exit_timer.start()

                    # 如果10秒后仍未退出，则强制退出
                    threading.Timer(10.0, lambda: os._exit(0)).start()
                else:
                    # 如果已经在关闭过程中，再次按Ctrl+C则强制退出
                    print("\n再次检测到Ctrl+C，强制退出...")
                    os._exit(0)
                return True  # 表示我们处理了这个事件
            return False

        # 设置控制台处理程序
        if not ctypes.windll.kernel32.SetConsoleCtrlHandler(console_ctrl_handler, True):
            print("警告: 无法设置Windows控制台处理程序")
    except Exception as e:
        print(f"设置Windows控制台处理程序时出错: {e}")


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
        global server_should_exit, force_exit_timer
        if not server_should_exit:
            print("\n正在优雅地关闭服务器...")
            server_should_exit = True
            should_exit.set()

            # 设置强制退出计时器
            if force_exit_timer is None:
                force_exit_timer = threading.Timer(5.0, force_exit)
                force_exit_timer.daemon = True
                force_exit_timer.start()

    # 注册退出处理函数
    atexit.register(lambda: print("服务器已关闭") if server_should_exit else None)

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
                await asyncio.wait_for(server_task, timeout=3.0)  # 缩短超时时间
                print("服务器已成功关闭")
                # 取消强制退出计时器
                if force_exit_timer and force_exit_timer.is_alive():
                    force_exit_timer.cancel()
            except asyncio.TimeoutError:
                print("服务器关闭超时，强制终止")
                server_task.cancel()
                try:
                    await asyncio.wait_for(server_task, timeout=1.0)  # 再给1秒时间
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    print("服务器任务已取消")
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
                await asyncio.wait_for(server_task, timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass


def handle_exception(exc_type, exc_value, exc_traceback):
    """自定义异常处理函数，用于优雅地处理KeyboardInterrupt"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 只打印简单的消息，不显示堆栈跟踪
        global server_should_exit, force_exit_timer
        if not server_should_exit:
            print("\n程序被用户中断，正在退出...")
            server_should_exit = True

            # 设置强制退出计时器
            if force_exit_timer is None:
                force_exit_timer = threading.Timer(5.0, force_exit)
                force_exit_timer.daemon = True
                force_exit_timer.start()
        return
    # 对于其他异常，使用默认处理方式
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


if __name__ == "__main__":
    # 设置自定义异常处理器
    sys.excepthook = handle_exception

    try:
        # 运行初始化和启动服务器
        asyncio.run(main())
    except KeyboardInterrupt:
        # 这里不需要额外的提示，因为信号处理器已经提供了关闭信息
        if not server_should_exit:
            print("\n程序已优雅退出")
        # 确保程序退出
        time.sleep(0.5)  # 给一点时间打印消息
        sys.exit(0)
    except Exception as e:
        import traceback

        print(f"程序异常退出: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        sys.exit(1)
