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


# 修复Windows环境下的asyncio ProactorBasePipeTransport _call_connection_lost错误
def patch_asyncio():
    """
    修复Windows环境下的asyncio ProactorBasePipeTransport _call_connection_lost错误
    这个错误通常在程序退出时出现，是由于Windows下的ProactorEventLoop在关闭时的一个已知问题
    """
    if sys.platform == "win32":
        # 仅在Windows环境下应用补丁
        try:
            import asyncio.proactor_events

            # 保存原始的_call_connection_lost方法
            original_call_connection_lost = (
                asyncio.proactor_events._ProactorBasePipeTransport._call_connection_lost
            )

            # 创建一个包装方法来捕获ConnectionResetError异常
            def _patched_call_connection_lost(self, exc):
                try:
                    return original_call_connection_lost(self, exc)
                except ConnectionResetError as e:
                    # 将错误转换为警告
                    if (
                        hasattr(self, "_loop")
                        and self._loop
                        and hasattr(self._loop, "get_debug")
                        and self._loop.get_debug()
                    ):
                        logging.warning(f"忽略连接关闭时的错误: {e}")
                    # 如果无法获取debug模式，也记录警告
                    else:
                        logging.warning(f"忽略连接关闭时的错误: {e}")
                except RuntimeError as e:
                    # 忽略"Event loop is closed"错误
                    if str(e) == "Event loop is closed":
                        if (
                            hasattr(self, "_loop")
                            and self._loop
                            and hasattr(self._loop, "get_debug")
                            and self._loop.get_debug()
                        ):
                            logging.warning(f"忽略事件循环已关闭的错误: {e}")
                        else:
                            logging.warning(f"忽略事件循环已关闭的错误: {e}")
                except Exception as e:
                    # 捕获所有其他可能的异常
                    logging.warning(f"在_call_connection_lost中捕获到异常: {e}")

            # 应用补丁
            asyncio.proactor_events._ProactorBasePipeTransport._call_connection_lost = (
                _patched_call_connection_lost
            )

            # 同样修复__del__方法中可能出现的问题
            original_del = asyncio.proactor_events._ProactorBasePipeTransport.__del__

            def _patched_del(self):
                try:
                    return original_del(self)
                except Exception as e:
                    logging.warning(f"忽略在__del__中的异常: {e}")

            # 应用__del__补丁
            asyncio.proactor_events._ProactorBasePipeTransport.__del__ = _patched_del

            print("已应用asyncio ProactorBasePipeTransport补丁")
        except (ImportError, AttributeError) as e:
            print(f"应用asyncio补丁失败: {e}")
        except Exception as e:
            print(f"应用asyncio补丁时发生未知错误: {e}")


# 强制退出函数
def force_exit():
    print("\n服务器关闭超时，强制退出...")
    # 确保所有线程都被终止
    import os
    import sys
    import signal
    import time

    # 在Unix/Linux/Mac系统上，尝试发送SIGKILL信号
    if sys.platform != "win32":
        try:
            # 在容器环境中，使用SIGTERM可能更合适
            pid = os.getpid()
            print(f"发送SIGTERM信号到进程 {pid}")
            os.kill(pid, signal.SIGTERM)
            # 给一点时间处理SIGTERM
            time.sleep(0.5)
            # 如果进程还在运行，使用SIGKILL
            print(f"发送SIGKILL信号到进程 {pid}")
            os.kill(pid, signal.SIGKILL)
        except Exception as e:
            print(f"发送信号失败: {e}")

    # 如果上面的方法失败，使用os._exit强制退出
    print("使用os._exit强制退出")
    os._exit(1)  # 使用非零退出码表示异常退出


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
            import threading  # 在函数内部导入threading模块

            if event in (CTRL_C_EVENT, CTRL_BREAK_EVENT):
                if not server_should_exit:
                    print("\n检测到Ctrl+C，正在优雅地关闭服务器...")
                    server_should_exit = True

                    # 设置强制退出计时器
                    if force_exit_timer is None:
                        force_exit_timer = threading.Timer(
                            3.0, force_exit
                        )  # 减少等待时间
                        force_exit_timer.daemon = True
                        force_exit_timer.start()

                    # 如果5秒后仍未退出，则强制退出
                    threading.Timer(5.0, lambda: os._exit(0)).start()  # 减少等待时间
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
    # 导入必要的模块
    import sys  # 确保在函数内部可以使用sys模块

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
        import threading  # 在函数内部导入threading模块
        import sys

        # 获取当前信号名称（如果可能）
        signal_name = "未知信号"
        try:
            import signal

            for sig_name in dir(signal):
                if sig_name.startswith("SIG") and not sig_name.startswith("SIG_"):
                    if getattr(signal, sig_name) == signal.getsignal(signal.SIGTERM):
                        signal_name = sig_name
                        break
        except:
            pass

        if not server_should_exit:
            print(f"\n收到{signal_name}信号，正在优雅地关闭服务器...")
            server_should_exit = True
            should_exit.set()

            # 设置强制退出计时器
            # 在容器环境中，我们需要更快地响应
            timeout = 2.0 if sys.platform != "win32" else 3.0
            if force_exit_timer is None:
                force_exit_timer = threading.Timer(timeout, force_exit)
                force_exit_timer.daemon = True
                force_exit_timer.start()
                print(f"已设置{timeout}秒后强制退出")

    # 注册退出处理函数
    atexit.register(lambda: print("服务器已关闭") if server_should_exit else None)

    # 添加信号处理器
    loop = asyncio.get_running_loop()
    try:
        # 在Linux/Unix系统上，特别处理SIGTERM信号（容器环境中常用）
        if sys.platform != "win32":
            print("在Unix/Linux环境中设置信号处理器")
            for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
                loop.add_signal_handler(sig, signal_handler)
                print(f"已注册信号处理器: {sig.name}")
        else:
            # 在Windows上只处理SIGINT和SIGTERM
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)
    except NotImplementedError:
        # Windows环境下可能不支持add_signal_handler
        import sys

        if sys.platform == "win32":
            print("Windows环境下使用替代信号处理方式")
            # 在Windows下使用替代方案
            import threading  # 确保在这里导入threading

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
            print("收到退出信号，开始关闭服务器...")
            # 正确关闭服务器
            if hasattr(server, "should_exit"):
                server.should_exit = True
                print("已设置服务器退出标志")

            # 等待服务器完成关闭过程
            try:
                # 在容器环境中，我们需要更快地响应退出信号
                print("等待服务器任务完成...")
                await asyncio.wait_for(
                    server_task, timeout=1.5
                )  # 在容器环境中使用更短的超时时间
                print("服务器已成功关闭")
                # 取消强制退出计时器
                if force_exit_timer and force_exit_timer.is_alive():
                    force_exit_timer.cancel()
                    print("已取消强制退出计时器")
            except asyncio.TimeoutError:
                print("服务器关闭超时，强制终止")
                server_task.cancel()
                try:
                    await asyncio.wait_for(
                        server_task, timeout=0.3
                    )  # 在容器环境中使用更短的超时时间
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    print("服务器任务已取消")
                # 确保强制退出计时器被取消
                if force_exit_timer and force_exit_timer.is_alive():
                    force_exit_timer.cancel()
                    print("强制退出计时器已取消")
            except asyncio.CancelledError:
                print("服务器已成功关闭")
                # 取消强制退出计时器
                if force_exit_timer and force_exit_timer.is_alive():
                    force_exit_timer.cancel()
                    print("已取消强制退出计时器")

            # 在容器环境中，确保所有资源都被释放
            print("正在清理资源...")
            # 关闭所有可能的连接池或资源
            try:
                from app.db.database import engine, sync_engine

                # 关闭异步引擎
                if engine:
                    # 异步引擎需要使用异步方法关闭
                    await engine.dispose()
                    print("异步数据库连接池已关闭")

                # 关闭同步引擎
                if sync_engine:
                    sync_engine.dispose()
                    print("同步数据库连接池已关闭")
            except ImportError as e:
                print(f"无法导入数据库引擎: {e}")
            except Exception as e:
                print(f"关闭数据库连接池时出错: {e}")
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
    import sys  # 确保在函数内部可以使用sys模块

    if issubclass(exc_type, KeyboardInterrupt):
        # 只打印简单的消息，不显示堆栈跟踪
        global server_should_exit, force_exit_timer
        import threading  # 在函数内部导入threading模块

        if not server_should_exit:
            print("\n程序被用户中断，正在退出...")
            server_should_exit = True

            # 设置强制退出计时器
            if force_exit_timer is None:
                force_exit_timer = threading.Timer(3.0, force_exit)  # 减少等待时间
                force_exit_timer.daemon = True
                force_exit_timer.start()
        return
    # 对于其他异常，使用默认处理方式
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


if __name__ == "__main__":
    # 应用asyncio补丁
    patch_asyncio()

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
