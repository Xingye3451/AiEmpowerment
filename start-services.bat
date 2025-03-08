@echo off
echo 创建Docker网络（如果不存在）...
docker network create aiempowerment-network 2>nul

echo 启动AI组件服务...
cd ai_components
call start.bat
cd ..

echo 启动主应用服务...
docker-compose up -d

echo 所有服务已启动
echo 后端API: http://localhost:8000/api/v1
echo 前端界面: http://localhost:80
echo RealESRGAN服务: http://localhost:6060
echo 字幕擦除服务: http://localhost:6061
echo 语音合成服务: http://localhost:6062
echo 唇形同步服务: http://localhost:6063

pause 