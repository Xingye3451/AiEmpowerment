import sys
import os
import importlib
import inspect


def check_sqlalchemy():
    """检查SQLAlchemy版本和可用的类"""
    print("检查SQLAlchemy版本和可用的类...\n")

    # 检查SQLAlchemy版本
    import sqlalchemy

    print(f"SQLAlchemy版本: {sqlalchemy.__version__}")

    # 检查是否有AsyncSession
    try:
        from sqlalchemy.ext.asyncio import AsyncSession

        print("成功从sqlalchemy.ext.asyncio导入AsyncSession")
    except ImportError:
        print("无法从sqlalchemy.ext.asyncio导入AsyncSession")

    try:
        from sqlalchemy.orm import AsyncSession

        print("成功从sqlalchemy.orm导入AsyncSession")
    except ImportError:
        print("无法从sqlalchemy.orm导入AsyncSession")

    # 检查sqlalchemy.ext.asyncio模块中的类
    print("\nsqlalchemy.ext.asyncio模块中的类:")
    try:
        import sqlalchemy.ext.asyncio

        for name, obj in inspect.getmembers(sqlalchemy.ext.asyncio):
            if inspect.isclass(obj):
                print(f"  - {name}")
    except ImportError:
        print("无法导入sqlalchemy.ext.asyncio模块")

    # 检查是否安装了异步数据库驱动
    print("\n检查异步数据库驱动:")
    for driver in ["aiosqlite", "aiomysql", "asyncpg"]:
        try:
            importlib.import_module(driver)
            print(f"  - {driver}: 已安装")
        except ImportError:
            print(f"  - {driver}: 未安装")

    # 检查requirements.txt中的SQLAlchemy相关依赖
    print("\n检查requirements.txt中的SQLAlchemy相关依赖:")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        req_file = os.path.join(backend_dir, "requirements.txt")

        if os.path.exists(req_file):
            with open(req_file, "r") as f:
                requirements = f.readlines()

            for req in requirements:
                req = req.strip()
                if (
                    "sqlalchemy" in req.lower()
                    or "aiosqlite" in req.lower()
                    or "aiomysql" in req.lower()
                ):
                    print(f"  - {req}")
        else:
            print("  未找到requirements.txt文件")
    except Exception as e:
        print(f"  读取requirements.txt时出错: {e}")


if __name__ == "__main__":
    check_sqlalchemy()
