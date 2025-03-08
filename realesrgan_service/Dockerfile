FROM pytorch/pytorch:1.9.1-cuda11.1-cudnn8-runtime

WORKDIR /app

# 安装基本依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装Real-ESRGAN
RUN pip install --no-cache-dir git+https://github.com/xinntao/Real-ESRGAN.git

# 下载预训练模型
RUN mkdir -p /app/models && \
    wget -O /app/models/RealESRGAN_x4plus.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth && \
    wget -O /app/models/RealESRGAN_x4plus_anime_6B.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth && \
    wget -O /app/models/RealESRGAN_x2plus.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth

# 创建目录
RUN mkdir -p /app/uploads/temp /app/uploads/processed_videos

# 复制应用代码
COPY app.py .

# 暴露端口
EXPOSE 6060

# 启动应用
CMD ["python", "app.py"] 