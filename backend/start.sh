#!/bin/sh

# 确保没有遗留的 Python 进程
pkill -9 python || true

# 等待进程完全终止
sleep 2

# 启动应用
exec python run.py 