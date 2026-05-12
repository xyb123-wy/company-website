#!/bin/bash
# 苏州清韵项目管理系统 - 服务器启动脚本
# 使用方法: bash start.sh

cd "$(dirname "$0")"

# 安装依赖
pip3 install -r requirements.txt -q

# 初始化数据库（如果不存在）
python3 -c "from models import init_db; init_db()"

# 启动服务
echo "网站启动中..."
gunicorn app:app -b 0.0.0.0:8000 --workers=2 --timeout=120
