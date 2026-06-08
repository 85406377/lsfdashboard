#!/bin/bash
# deploy.sh — CentOS 7.9 部署脚本（需 root 权限）
# 用法: sudo bash deploy.sh

set -e

APP_DIR="/opt/lsf-monitor"
DATA_DIR="/var/lib/lsf-monitor"
LOG_DIR="/var/log/lsf-monitor"
RUN_USER="lsfmon"
RUN_GROUP="lsf"

echo "=========================================="
echo " LSF Monitor 部署脚本"
echo "=========================================="

# ── 1. 检查 python3 ──
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] 未找到 python3，请先安装 Python 3"
    exit 1
fi

# ── 2. 检查 LSF 命令 ──
for cmd in lsload busers; do
    if ! command -v $cmd &>/dev/null; then
        echo "[WARN] 未找到 '$cmd' 命令，请确认 LSF 客户端已安装且在 PATH 中"
    fi
done

# ── 3. 创建运行用户（若不存在）─────────────────
if ! id "$RUN_USER" &>/dev/null; then
    echo "[STEP 1/6] 创建系统用户 '$RUN_USER'"
    groupadd -f "$RUN_GROUP"
    useradd -g "$RUN_GROUP" -d /home/"$RUN_USER" -s /sbin/nologin "$RUN_USER" 2>/dev/null || \
    useradd -g "$RUN_GROUP" -s /sbin/nologin "$RUN_USER"
else
    echo "[STEP 1/6] 用户 '$RUN_USER' 已存在，跳过"
fi

# ── 4. 创建目录 ──
echo "[STEP 2/6] 创建目录..."
for d in "$APP_DIR" "$DATA_DIR" "$LOG_DIR"; do
    if [ ! -d "$d" ]; then
        mkdir -p "$d"
        echo "  创建 $d"
    fi
done

# ── 5. 拷贝文件 ──
echo "[STEP 3/6] 拷贝项目文件..."
# 已知脚本自身路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/collect.py"    "$APP_DIR/"
cp "$SCRIPT_DIR/db.py"         "$APP_DIR/"
cp "$SCRIPT_DIR/stats.py"      "$APP_DIR/"
cp "$SCRIPT_DIR/config.json"   "$APP_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$APP_DIR/"

# ── 6. 安装依赖 ──
echo "[STEP 4/6] 安装 Python 依赖..."
pip3 install --quiet DBUtils 2>/dev/null || pip3 install DBUtils

# ── 7. 目录权限 ──
echo "[STEP 5/6] 设置权限..."
chown -R "$RUN_USER:$RUN_GROUP" "$APP_DIR" "$DATA_DIR" "$LOG_DIR"
chmod 755 "$APP_DIR/collect.py"
chmod 755 "$APP_DIR/stats.py"
chmod 644 "$APP_DIR/config.json"

# ── 8. systemd ──
SERVICE_FILE="/etc/systemd/system/lsf-monitor.service"
echo "[STEP 6/6] 部署 systemd service..."
if [ -f "$SCRIPT_DIR/lsf-monitor.service" ]; then
    cp "$SCRIPT_DIR/lsf-monitor.service" "$SERVICE_FILE"
    systemctl daemon-reload
    systemctl enable lsf-monitor
    echo "Service 已安装，可通过 'systemctl start lsf-monitor' 启动"
else
    echo "[WARN] 未找到 lsf-monitor.service，跳过 systemd 安装"
    echo "       可手动使用: nohup python3 $APP_DIR/collect.py &"
fi

echo ""
echo "=========================================="
echo " 部署完成！"
echo "=========================================="
echo "  配置目录: $APP_DIR"
echo "  数据目录: $DATA_DIR"
echo "  日志目录: $LOG_DIR"
echo ""
echo "  启动命令（systemd）: systemctl start lsf-monitor"
echo "  查看日志: journalctl -u lsf-monitor -f"
echo "  查询统计: python3 $APP_DIR/stats.py overview"
echo "=========================================="