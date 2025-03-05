import subprocess
import sys
import os


def fix_sqlalchemy():
    """安装正确版本的SQLAlchemy"""
    print("正在安装正确版本的SQLAlchemy...")

    # 安装SQLAlchemy 1.4.x版本
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "sqlalchemy>=1.4.23,<2.0.0"],
        check=True,
    )

    # 检查安装结果
    import sqlalchemy

    print(f"安装完成，当前SQLAlchemy版本: {sqlalchemy.__version__}")

    # 检查是否有AsyncSession
    try:
        from sqlalchemy.ext.asyncio import AsyncSession

        print("成功从sqlalchemy.ext.asyncio导入AsyncSession")
    except ImportError:
        print("无法从sqlalchemy.ext.asyncio导入AsyncSession")

    print("\n安装完成，请重新启动应用程序。")


if __name__ == "__main__":
    fix_sqlalchemy()
