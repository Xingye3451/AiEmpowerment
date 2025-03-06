from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import logging
import asyncio
import os
from app.api.api import api_router
from app.core.config import settings
from app.core.scheduler import init_scheduler, shutdown_scheduler
from app.core.task_queue import TaskQueue
from app.db.database import engine
from app.db.init_db import init_db, ensure_db_exists
from app.db.migrations.run_migrations import run_all_migrations
from app.db.base_class import Base
from fastapi import status
from fastapi.exceptions import RequestValidationError, HTTPException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# 禁用 SQLAlchemy 的日志
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# 确保数据库文件存在
ensure_db_exists()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # 明确允许前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["X-Process-Time"],
)


# 添加请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 添加异常处理中间件
@app.middleware("http")
async def log_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        # 记录异常信息
        logger.error(f"请求处理异常: {request.method} {request.url}")
        logger.error(f"异常类型: {type(e).__name__}")
        logger.error(f"异常信息: {str(e)}")

        # 记录请求信息
        logger.error(f"请求头: {request.headers}")
        body = await request.body()
        if body:
            try:
                logger.error(f"请求体: {body.decode()}")
            except:
                logger.error(f"请求体: 无法解码")

        # 重新抛出异常，让FastAPI的异常处理器处理
        raise


# 添加API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


# 添加全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"请求验证错误: {request.method} {request.url}")
    logger.error(f"错误详情: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": f"请求验证错误: {exc.errors()}"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP异常: {request.method} {request.url}")
    logger.error(f"状态码: {exc.status_code}, 详情: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {request.method} {request.url}")
    logger.error(f"异常类型: {type(exc).__name__}, 详情: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("应用启动")
    # 初始化数据库
    await init_db()
    # 运行数据库迁移
    await run_all_migrations()
    # 初始化调度器
    init_scheduler()

    # 初始化任务队列
    task_queue = TaskQueue()
    await task_queue.initialize()
    logger.info("任务队列已初始化")

    # 确保静态文件目录存在
    os.makedirs("static/previews", exist_ok=True)
    os.makedirs("static/videos", exist_ok=True)
    os.makedirs("uploads/videos", exist_ok=True)
    os.makedirs("uploads/processed_videos", exist_ok=True)
    logger.info("静态文件和上传目录已创建")

    # 挂载静态文件目录
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info("静态文件目录已挂载")
    except Exception as e:
        logger.error(f"挂载静态文件目录失败: {str(e)}")

    # 直接在main.py中实现patch_asyncio函数
    def patch_asyncio():
        """
        修复Windows环境下的asyncio ProactorBasePipeTransport _call_connection_lost错误
        这个错误通常在程序退出时出现，是由于Windows下的ProactorEventLoop在关闭时的一个已知问题
        """
        import sys

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
                original_del = (
                    asyncio.proactor_events._ProactorBasePipeTransport.__del__
                )

                def _patched_del(self):
                    try:
                        return original_del(self)
                    except Exception as e:
                        logging.warning(f"忽略在__del__中的异常: {e}")

                # 应用__del__补丁
                asyncio.proactor_events._ProactorBasePipeTransport.__del__ = (
                    _patched_del
                )

                logger.info("已应用asyncio ProactorBasePipeTransport补丁")
            except (ImportError, AttributeError) as e:
                logger.error(f"应用asyncio补丁失败: {e}")
            except Exception as e:
                logger.error(f"应用asyncio补丁时发生未知错误: {e}")

    # 应用asyncio补丁
    try:
        patch_asyncio()
    except Exception as e:
        logger.error(f"应用asyncio补丁时出错: {e}")


# 应用关闭事件
@app.on_event("shutdown")
def shutdown_event():
    logger.info("应用关闭")
    # 关闭调度器
    shutdown_scheduler()


@app.get("/")
def root():
    return {"message": "欢迎使用AI赋能内容分发平台API"}
