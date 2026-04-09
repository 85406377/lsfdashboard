#!/bin/bash
# =========================================
# IBM LSF Dashboard 一键安装脚本
# 适用系统：Rocky Linux 8.10 / RHEL 8 / CentOS 8
# =========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 用户运行此脚本"
        exit 1
    fi
}

# 检查系统版本
check_system() {
    log_info "检查系统版本..."
    
    if [ -f /etc/redhat-release ]; then
        SYSTEM_VERSION=$(cat /etc/redhat-release)
        log_info "系统版本：$SYSTEM_VERSION"
        
        # 检查是否是 Rocky/CentOS/RHEL 8.x
        if echo "$SYSTEM_VERSION" | grep -qE "(Rocky|CentOS|Red Hat).*(8\.[0-9])"; then
            log_success "系统版本符合要求"
        else
            log_warn "系统可能不兼容，继续尝试安装..."
        fi
    else
        log_error "非 RHEL 系系统，可能不兼容"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    log_info "安装系统依赖..."
    
    yum install -y epel-release
    yum install -y \
        python3 \
        python3-pip \
        python3-devel \
        gcc \
        nodejs \
        npm \
        git \
        wget \
        curl
    
    log_success "系统依赖安装完成"
}

# 检查并安装 Node.js (如果版本太低)
check_nodejs() {
    log_info "检查 Node.js 版本..."
    
    NODE_VERSION=$(node -v 2>/dev/null || echo "not installed")
    log_info "当前 Node.js 版本：$NODE_VERSION"
    
    # 如果版本低于 16，安装新版本
    if [ "$NODE_VERSION" != "not installed" ]; then
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
        if [ "$NODE_MAJOR" -lt 16 ]; then
            log_warn "Node.js 版本过低，需要升级到 16+"
            log_info "安装 Node.js 18..."
            
            curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
            yum install -y nodejs
            
            log_success "Node.js 升级完成"
        fi
    else
        log_info "安装 Node.js 18..."
        curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
        yum install -y nodejs
        log_success "Node.js 安装完成"
    fi
}

# 安装 Python 依赖
install_python_deps() {
    log_info "安装 Python 依赖..."
    
    cd "$(dirname "$0")/backend"
    
    # 升级 pip
    pip3 install --upgrade pip
    
    # 安装依赖
    pip3 install -r requirements.txt
    
    log_success "Python 依赖安装完成"
}

# 安装前端依赖并构建
build_frontend() {
    log_info "构建前端..."
    
    cd "$(dirname "$0")/frontend"
    
    # 清理旧的 node_modules
    if [ -d "node_modules" ]; then
        log_info "清理旧的 node_modules..."
        rm -rf node_modules package-lock.json
    fi
    
    # 安装依赖
    log_info "安装前端依赖 (这可能需要几分钟)..."
    npm install
    
    # 构建
    log_info "构建前端..."
    npm run build
    
    log_success "前端构建完成"
}

# 配置防火墙
config_firewall() {
    log_info "配置防火墙..."
    
    # 检查 firewalld 状态
    if systemctl is-active --quiet firewalld; then
        # 添加防火墙规则
        firewall-cmd --permanent --add-port=5002/tcp
        firewall-cmd --reload
        log_success "防火墙配置完成 (端口 5002)"
    else
        log_warn "firewalld 未运行，跳过防火墙配置"
    fi
}

# 创建 systemd 服务
create_systemd_service() {
    log_info "创建 systemd 服务..."
    
    INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
    
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

    # 重载 systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable lsf-dashboard.service
    
    log_success "systemd 服务创建完成"
}

# 启动服务
start_service() {
    log_info "启动 LSF Dashboard 服务..."
    
    systemctl start lsf-dashboard.service
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet lsf-dashboard.service; then
        log_success "服务启动成功!"
    else
        log_error "服务启动失败，请检查日志"
        systemctl status lsf-dashboard.service
        exit 1
    fi
}

# 显示访问信息
show_info() {
    echo ""
    echo "========================================="
    echo -e "${GREEN}  LSF Dashboard 安装完成!${NC}"
    echo "========================================="
    echo ""
    
    # 获取本机 IP
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    HOSTNAME=$(hostname)
    
    echo "访问地址:"
    echo "  - 本地访问：http://localhost:5002"
    echo "  - 局域网访问：http://$LOCAL_IP:5002"
    echo "  - 主机名访问：http://$HOSTNAME:5002"
    echo ""
    echo "服务管理命令:"
    echo "  - 启动：systemctl start lsf-dashboard"
    echo "  - 停止：systemctl stop lsf-dashboard"
    echo "  - 重启：systemctl restart lsf-dashboard"
    echo "  - 状态：systemctl status lsf-dashboard"
    echo "  - 开机自启：systemctl enable lsf-dashboard"
    echo ""
    echo "日志查看:"
    echo "  - journalctl -u lsf-dashboard -f"
    echo ""
    echo "========================================="
}

# 主函数
main() {
    echo ""
    echo "========================================="
    echo "  IBM LSF Dashboard 一键安装脚本"
    echo "  适用系统：Rocky Linux 8.10"
    echo "========================================="
    echo ""
    
    check_root
    check_system
    install_system_deps
    check_nodejs
    install_python_deps
    build_frontend
    config_firewall
    create_systemd_service
    start_service
    show_info
}

# 运行主函数
main "$@"
