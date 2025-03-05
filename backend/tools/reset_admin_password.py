import sqlite3
import os
import bcrypt
import sys


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def reset_admin_password(new_password: str = "admin123456"):
    """重置管理员密码"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    db_path = os.path.join(backend_dir, "app.db")

    print(f"数据库路径: {db_path}")

    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查admin用户是否存在
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()

        if not admin:
            print("错误: 管理员用户不存在")
            return False

        # 生成新密码哈希
        hashed_password = get_password_hash(new_password)

        # 更新管理员密码
        cursor.execute(
            "UPDATE users SET hashed_password = ? WHERE username = 'admin'",
            (hashed_password,),
        )

        # 提交更改
        conn.commit()

        # 验证更改
        cursor.execute("SELECT hashed_password FROM users WHERE username = 'admin'")
        updated_hash = cursor.fetchone()[0]

        print(f"管理员密码已重置")
        print(f"新密码: {new_password}")
        print(f"新密码哈希: {updated_hash}")

        # 关闭连接
        conn.close()

        return True

    except Exception as e:
        print(f"重置密码时出错: {e}")
        return False


if __name__ == "__main__":
    # 如果提供了命令行参数，使用它作为新密码
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
        reset_admin_password(new_password)
    else:
        # 否则使用默认密码
        reset_admin_password()
