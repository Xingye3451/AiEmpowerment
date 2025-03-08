@echo off
echo 停止主应用服务...
docker-compose down

echo 停止AI组件服务...
cd ai_components
call stop.bat
cd ..

echo 所有服务已停止

pause 