import requests
import json
import sys
import os
import time

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)


def test_notifications_api(username="admin", password="admin123456"):
    """测试通知相关的API"""
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

        # 设置请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # 2. 获取通知计数
        count_url = f"{base_url}/notifications/count"
        print(f"\n尝试获取通知计数: {count_url}")

        count_response = requests.get(count_url, headers=headers)

        print(f"响应状态码: {count_response.status_code}")
        print(f"响应内容: {count_response.text}")

        if count_response.status_code != 200:
            print(f"获取通知计数失败: {count_response.text}")
            return False

        # 3. 获取通知列表
        list_url = f"{base_url}/notifications"
        print(f"\n尝试获取通知列表: {list_url}")

        list_response = requests.get(list_url, headers=headers)

        print(f"响应状态码: {list_response.status_code}")
        print(
            f"响应内容摘要: {json.dumps(list_response.json(), ensure_ascii=False)[:200]}..."
        )

        if list_response.status_code != 200:
            print(f"获取通知列表失败: {list_response.text}")
            return False

        # 如果有通知，测试标记为已读和删除功能
        notifications = list_response.json().get("items", [])
        if notifications:
            notification = notifications[0]
            notification_id = notification["id"]

            # 4. 获取通知详情
            detail_url = f"{base_url}/notifications/{notification_id}"
            print(f"\n尝试获取通知详情: {detail_url}")

            detail_response = requests.get(detail_url, headers=headers)

            print(f"响应状态码: {detail_response.status_code}")
            print(f"响应内容: {detail_response.text}")

            if detail_response.status_code != 200:
                print(f"获取通知详情失败: {detail_response.text}")

            # 5. 标记通知为已读
            read_url = f"{base_url}/notifications/{notification_id}/read"
            print(f"\n尝试标记通知为已读: {read_url}")

            read_response = requests.post(read_url, headers=headers)

            print(f"响应状态码: {read_response.status_code}")
            print(f"响应内容: {read_response.text}")

            if read_response.status_code != 200:
                print(f"标记通知为已读失败: {read_response.text}")

            # 6. 标记所有通知为已读
            read_all_url = f"{base_url}/notifications/read-all"
            print(f"\n尝试标记所有通知为已读: {read_all_url}")

            read_all_response = requests.post(read_all_url, headers=headers)

            print(f"响应状态码: {read_all_response.status_code}")
            print(f"响应内容: {read_all_response.text}")

            if read_all_response.status_code != 200:
                print(f"标记所有通知为已读失败: {read_all_response.text}")

            # 7. 删除通知
            delete_url = f"{base_url}/notifications/{notification_id}"
            print(f"\n尝试删除通知: {delete_url}")

            delete_response = requests.delete(delete_url, headers=headers)

            print(f"响应状态码: {delete_response.status_code}")
            print(f"响应内容: {delete_response.text}")

            if delete_response.status_code != 200:
                print(f"删除通知失败: {delete_response.text}")
        else:
            print("\n没有通知可供测试标记为已读和删除功能")

        print("\n所有API测试完成")
        return True

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return False


if __name__ == "__main__":
    # 如果提供了命令行参数，使用它们作为参数
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
        test_notifications_api(username, password)
    elif len(sys.argv) > 1:
        # 如果只提供了一个参数，假设它是密码
        password = sys.argv[1]
        test_notifications_api(password=password)
    else:
        # 否则使用默认参数
        test_notifications_api()
