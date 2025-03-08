#!/bin/bash

# 创建Docker网络（如果不存在）
docker network create aiempowerment-network 2>/dev/null || true

# 创建标准目录结构
echo "创建标准目录结构..."
mkdir -p uploads/temp uploads/processed uploads/original
mkdir -p static/images static/videos static/previews
mkdir -p data/models data/configs data/logs
chmod -R 777 uploads static data

echo "启动AI组件服务..."
cd ai_components
./start.sh
cd ..

echo "启动主应用服务..."
docker-compose up -d

echo "所有服务已启动"
echo "后端API: http://localhost:8000/api/v1"
echo "前端界面: http://localhost:80"
echo "RealESRGAN服务: http://localhost:5003"
echo "字幕擦除服务: http://localhost:5000"
echo "语音合成服务: http://localhost:5001"
echo "唇形同步服务: http://localhost:5002" 