#!/bin/bash
# =========================================
# IBM LSF Dashboard 离线安装脚本
# 适用系统：Rocky Linux 8.10 / RHEL 8 / CentOS 8
# =========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查是否 root
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 用户运行此脚本"
    exit 1
fi

INSTALL_DIR="/opt/lsf-dashboard"

log_info "开始安装 LSF Dashboard..."

# 解压源码包
log_info "解压源码包..."
tar -xzf lsf-dashboard-src.tar.gz -C /tmp/

# 创建安装目录
mkdir -p $INSTALL_DIR

# 复制文件
log_info "复制文件到 $INSTALL_DIR..."
cp -r /tmp/backend $INSTALL_DIR/
cp -r /tmp/frontend $INSTALL_DIR/
cp -r /tmp/README.md $INSTALL_DIR/
cp -r /tmp/start.sh $INSTALL_DIR/

# 安装 Python 依赖
log_info "安装 Python 依赖..."
cd $INSTALL_DIR/backend
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 安装前端依赖并构建
log_info "构建前端..."
cd $INSTALL_DIR/frontend

# 检查 node_modules 是否存在
if [ -d "../../node_modules_cache" ]; then
    log_info "使用缓存的 node_modules..."
    cp -r ../../node_modules_cache ./node_modules
else
    log_info "安装前端依赖..."
    npm install
fi

npm run build

# 创建 systemd 服务
log_info "创建 systemd 服务..."
cat > /etc/systemd/system/lsf-dashboard.service << EOF
[Unit]
Description=IBM LSF Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/backend
ExecStart=/usr/bin/python3 $INSTALL_DIR/backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable lsf-dashboard.service

# 配置防火墙
if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-port=5002/tcp
    firewall-cmd --reload
fi

# 启动服务
log_info "启动服务..."
systemctl start lsf-dashboard.service
sleep 3

# 显示信息
LOCAL_IP=$(hostname -I | awk '{print $1}')
HOSTNAME=$(hostname)

echo ""
echo "========================================="
echo -e "${GREEN}  LSF Dashboard 安装完成!${NC}"
echo "========================================="
echo ""
echo "访问地址:"
echo "  - 本地访问：http://localhost:5002"
echo "  - 局域网访问：http://$LOCAL_IP:5002"
echo "  - 主机名访问：http://$HOSTNAME:5002"
echo ""
echo "服务管理:"
echo "  - systemctl start|stop|restart|status lsf-dashboard"
echo ""
echo "========================================="
