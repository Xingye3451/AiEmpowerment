#!/bin/bash
echo "开始构建AI组件镜像..."

echo "1. 构建基础镜像 aiempowerment-base:latest"
docker build -t aiempowerment-base:latest -f ai_components/base.Dockerfile ai_components

echo "2. 构建Real-ESRGAN镜像"
docker build -t aiempowerment-realesrgan:latest -f ai_components/Real-ESRGAN/Dockerfile.standalone ai_components/Real-ESRGAN

echo "3. 构建视频字幕移除镜像"
docker build -t aiempowerment-video-subtitle-remover:latest -f ai_components/video-subtitle-remover/Dockerfile.standalone ai_components/video-subtitle-remover

echo "4. 构建VALL-E-X镜像"
docker build -t aiempowerment-vall-e-x:latest -f ai_components/VALL-E-X/Dockerfile.standalone ai_components/VALL-E-X

echo "5. 构建Wav2Lip镜像"
docker build -t aiempowerment-wav2lip:latest -f ai_components/Wav2Lip/Dockerfile.standalone ai_components/Wav2Lip

echo "所有AI组件镜像构建完成！"
docker images | grep aiempowerment 