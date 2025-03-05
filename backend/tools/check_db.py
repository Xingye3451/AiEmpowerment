import sqlite3
import os
import json

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
db_path = os.path.join(backend_dir, "app.db")

print(f"数据库路径: {db_path}")
print(f"数据库文件是否存在: {os.path.exists(db_path)}")

try:
    # 连接数据库
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使用命名行
    cursor = conn.cursor()

    # 检查users表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        print("users表存在")

        # 获取表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\n用户表结构:")
        for col in columns:
            print(
                f"{col[0]}: {col[1]} ({col[2]}), 非空: {col[3]}, 默认值: {col[4]}, 主键: {col[5]}"
            )

        # 获取用户数据
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        print("\n用户数据:")
        if rows:
            for row in rows:
                row_dict = dict(row)
                print("\n用户ID:", row_dict["id"])
                print("邮箱:", row_dict["email"])
                print("用户名:", row_dict["username"])
                print("密码哈希:", row_dict["hashed_password"])
                print("是否激活:", row_dict["is_active"])
                print("是否超级用户:", row_dict["is_superuser"])
                print("角色:", row_dict["role"])
        else:
            print("没有用户数据")
    else:
        print("users表不存在")

        # 列出所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\n数据库中的表:")
        for table in tables:
            print(table[0])

    # 关闭连接
    conn.close()

except Exception as e:
    print(f"检查数据库时出错: {e}")
