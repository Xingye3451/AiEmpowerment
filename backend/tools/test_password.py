import bcrypt
import os
import sqlite3


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        # 尝试直接验证
        result1 = bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        print(f"方法1结果: {result1}")

        # 尝试不编码哈希值
        result2 = bcrypt.checkpw(
            plain_password.encode(), hashed_password.encode("utf-8")
        )
        print(f"方法2结果: {result2}")

        return result1 or result2
    except Exception as e:
        print(f"验证密码时出错: {e}")
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
db_path = os.path.join(backend_dir, "app.db")

# 从数据库获取存储的哈希值
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT hashed_password FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    if result:
        stored_hash = result[0]
    else:
        stored_hash = None
        print("未找到admin用户")
    conn.close()
except Exception as e:
    print(f"从数据库获取哈希值时出错: {e}")
    stored_hash = None

# 如果没有从数据库获取到哈希值，使用之前的值
if not stored_hash:
    stored_hash = "$2b$12$DoW/VlUnWeNmBPJa6a3feuBB/4/aRV9JXYo7Kg8FPMgBOESAQXgTG"

# 测试默认密码
test_password = "admin123456"

print(f"存储的哈希值: {stored_hash}")
print(f"测试密码: {test_password}")

# 验证密码
is_valid = verify_password(test_password, stored_hash)
print(f"密码验证结果: {is_valid}")

# 生成新的哈希值进行比较
new_hash = get_password_hash(test_password)
print(f"新生成的哈希值: {new_hash}")
print(f"新哈希值与存储哈希值比较: {new_hash == stored_hash}")

# 验证新生成的哈希值
is_new_valid = verify_password(test_password, new_hash)
print(f"新哈希值验证结果: {is_new_valid}")

# 尝试直接使用bcrypt验证
try:
    result = bcrypt.checkpw(test_password.encode(), stored_hash.encode())
    print(f"直接使用bcrypt验证结果: {result}")
except Exception as e:
    print(f"直接使用bcrypt验证时出错: {e}")
