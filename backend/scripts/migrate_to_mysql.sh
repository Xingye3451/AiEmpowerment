#!/bin/bash

echo "==================================="
echo "SQLite到MySQL数据迁移工具"
echo "==================================="
echo ""

# 检查Python是否安装
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python，请安装Python并确保添加到PATH中。"
    exit 1
fi

# 安装依赖
echo "正在安装必要的依赖..."
pip install pymysql tqdm pyyaml

# 执行迁移脚本
echo ""
echo "开始执行数据迁移..."
python migrate_sqlite_to_mysql.py

if [ $? -ne 0 ]; then
    echo ""
    echo "迁移过程中出现错误，请查看日志文件了解详情。"
else
    echo ""
    echo "迁移成功完成！"
fi

echo ""
echo "按Enter键退出..."
read 