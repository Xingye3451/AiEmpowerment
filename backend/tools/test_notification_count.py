import requests
import json
import sys
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)


def test_notification_count(username="admin", password="admin123456"):
    """测试通知计数API"""
    base_url = "http://localhost:8000/api/v1"

    # 1. 登录获取token
    login_url = f"{base_url}/auth/login/admin"
    login_data = {"username": username, "password": password}

    print(f"尝试登录: {login_url}")
    print(f"登录数据: {json.dumps(login_data, ensure_ascii=False)}")

    try:
        login_response = requests.post(login_url, data=login_data)
        login_response.raise_for_status()
        token = login_response.json().get("access_token")

        if not token:
            print("登录失败: 未获取到token")
            return False

        print("登录成功，获取到token")

        # 2. 获取通知计数
        count_url = f"{base_url}/notifications/count"
        headers = {"Authorization": f"Bearer {token}"}

        print(f"\n尝试获取通知计数: {count_url}")
        print(f"请求头: {headers}")

        count_response = requests.get(count_url, headers=headers)

        print(f"响应状态码: {count_response.status_code}")
        print(f"响应内容: {count_response.text}")

        if count_response.status_code == 200:
            print("获取通知计数成功")
            return True
        else:
            print(f"获取通知计数失败: {count_response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return False


if __name__ == "__main__":
    # 如果提供了命令行参数，使用它们作为参数
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
        test_notification_count(username, password)
    elif len(sys.argv) > 1:
        # 如果只提供了一个参数，假设它是密码
        password = sys.argv[1]
        test_notification_count(password=password)
    else:
        # 否则使用默认参数
        test_notification_count()
