#!/bin/bash
# LSF Dashboard 启动脚本

echo "==================================="
echo "  IBM LSF 作业监控 Dashboard"
echo "==================================="

# 检查 Python 版本
echo ""
echo "检查 Python 环境..."
python --version

# 安装后端依赖
echo ""
echo "安装后端依赖..."
cd backend
pip install -r requirements.txt

# 检查前端是否已构建
if [ ! -d "../frontend/dist" ]; then
    echo ""
    echo "构建前端..."
    cd ../frontend
    npm install
    npm run build
    cd ..
fi

# 启动后端服务
echo ""
echo "启动后端服务..."
cd backend
python app.py
