import requests
import json


def test_tts():
    url = "http://localhost:5001/api/tts"
    payload = {
        "text": "你好，这是一个测试。Hello, this is a test.",
        "language": "auto",
        "accent": "no-accent",
    }

    headers = {"Content-Type": "application/json", "Accept": "audio/wav"}

    try:
        print("发送请求到VALL-E-X服务...")
        response = requests.post(url, json=payload, headers=headers)

        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")

        if response.status_code == 200:
            with open("test_output.wav", "wb") as f:
                f.write(response.content)
            print("语音生成成功，已保存为test_output.wav")
        else:
            print(f"错误: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"发生异常: {e}")


def test_status():
    url = "http://localhost:5001/status"

    try:
        print("检查VALL-E-X服务状态...")
        response = requests.get(url)

        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"服务状态: {response.json()}")
        else:
            print(f"错误: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"发生异常: {e}")


if __name__ == "__main__":
    # 首先检查服务状态
    test_status()

    # 然后测试TTS功能
    test_tts()
