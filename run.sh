#!/bin/bash
# Wattpad Downloader 启动脚本

echo "正在启动 Wattpad Downloader..."
echo "访问地址: http://localhost:8000"
echo ""

# 确保依赖已安装
if [ ! -d ".venv" ]; then
    echo "正在安装依赖..."
    uv sync
fi

# 使用 uv 运行应用（自动管理虚拟环境）
uv run --python 3.11 chainlit run app.py --port 8000
