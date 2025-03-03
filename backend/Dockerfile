FROM python:3.13.0-slim


WORKDIR /app

# 设置pip使用阿里云镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip config set install.trusted-host mirrors.aliyun.com

# 复制项目文件
COPY requirements.txt .
COPY run.py .
COPY app/ app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir email-validator

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "run.py"]