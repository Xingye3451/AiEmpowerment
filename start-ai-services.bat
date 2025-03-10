@echo off
echo 开始启动AI组件服务...

echo 1. 创建必要的目录
if not exist uploads mkdir uploads
if not exist uploads\temp mkdir uploads\temp
if not exist uploads\processed mkdir uploads\processed
if not exist static mkdir static
if not exist data mkdir data

echo 2. 创建Docker网络
docker network create --driver bridge aiempowerment-network 2>nul || echo 网络已存在

echo 3. 启动AI组件服务
cd ai_components
docker-compose up -d

echo 4. 检查服务状态
timeout /t 5
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | findstr aiempowerment

echo AI组件服务已启动！
echo 服务访问地址:
echo - 视频字幕移除: http://localhost:5000/status
echo - VALL-E-X语音合成: http://localhost:5001/status
echo - Wav2Lip唇形同步: http://localhost:5002/status
echo - Real-ESRGAN超分辨率: http://localhost:5003/status

pause 