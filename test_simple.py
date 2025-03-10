import requests

# 检查服务状态
print("检查VALL-E-X服务状态...")
status_response = requests.get("http://localhost:5001/status")
print(f"状态码: {status_response.status_code}")
if status_response.status_code == 200:
    print(f"服务状态: {status_response.json()}")

# 测试TTS功能
print("\n发送简单的TTS请求...")
tts_response = requests.post(
    "http://localhost:5001/api/tts",
    json={"text": "测试", "language": "zh", "accent": "no-accent"},
)

print(f"状态码: {tts_response.status_code}")
if tts_response.status_code == 200:
    with open("simple_test.wav", "wb") as f:
        f.write(tts_response.content)
    print("语音生成成功，已保存为simple_test.wav")
else:
    print(f"错误响应: {tts_response.text}")
