#!/bin/bash
echo "停止AI组件服务..."

cd ai_components
docker-compose down

echo "检查是否有残留容器..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep aiempowerment

echo "AI组件服务已停止！" 