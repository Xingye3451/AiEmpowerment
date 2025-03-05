import requests
import json
import sys
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)


def test_admin_password_change(
    admin_username="admin", current_password="admin123456", new_password="admin123456"
):
    """测试管理员密码修改功能"""
    base_url = "http://localhost:8000/api/v1"

    # 1. 登录获取token
    login_url = f"{base_url}/auth/login/admin"
    login_data = {"username": admin_username, "password": current_password}

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

        # 2. 修改密码
        change_password_url = f"{base_url}/admin/change-password"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        password_data = {
            "current_password": current_password,
            "new_password": new_password,
        }

        print(f"\n尝试修改密码: {change_password_url}")
        print(f"密码修改数据: {json.dumps(password_data, ensure_ascii=False)}")
        print(f"请求头: {headers}")

        change_response = requests.put(
            change_password_url, headers=headers, json=password_data
        )

        print(f"响应状态码: {change_response.status_code}")
        print(f"响应内容: {change_response.text}")

        if change_response.status_code == 200:
            print("密码修改成功")
            print(
                "\n注意: 在前端应用中，密码修改成功后会自动退出登录并重定向到登录页面"
            )

            # 3. 尝试使用新密码登录
            if current_password != new_password:
                print("\n尝试使用新密码登录...")
                login_data["password"] = new_password
                login_response = requests.post(login_url, data=login_data)
                if login_response.status_code == 200:
                    print("使用新密码登录成功")
                else:
                    print(f"使用新密码登录失败: {login_response.text}")

            return True
        else:
            print(f"密码修改失败: {change_response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return False


if __name__ == "__main__":
    # 如果提供了命令行参数，使用它们作为参数
    if len(sys.argv) > 3:
        admin_username = sys.argv[1]
        current_password = sys.argv[2]
        new_password = sys.argv[3]
        test_admin_password_change(admin_username, current_password, new_password)
    elif len(sys.argv) > 1:
        # 如果只提供了一个参数，假设它是当前密码
        current_password = sys.argv[1]
        test_admin_password_change(
            current_password=current_password, new_password=current_password
        )
    else:
        # 否则使用默认参数
        test_admin_password_change()
