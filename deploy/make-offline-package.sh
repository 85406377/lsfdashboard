#!/bin/bash
# =========================================
# 制作离线安装包脚本
# =========================================

set -e

echo "========================================="
echo "  制作 LSF Dashboard 离线安装包"
echo "========================================="

WORK_DIR="/tmp/lsf-offline-package"
rm -rf $WORK_DIR
mkdir -p $WORK_DIR/{deploy,python-deps,node-deps}

# 1. 复制部署文件
echo "[1/4] 复制部署文件..."
cp -r /root/.openclaw/workspace/lsf-dashboard/deploy/* $WORK_DIR/deploy/

# 2. 下载 Python 依赖
echo "[2/4] 下载 Python 依赖..."
cd $WORK_DIR/python-deps
pip3 download Flask Flask-CORS Werkzeug Jinja2 MarkupSafe itsdangerous click -d .

# 3. 下载 Node.js
echo "[3/4] 下载 Node.js 18..."
cd $WORK_DIR/node-deps
NODE_PKG="node-v18.19.0-linux-x64.tar.xz"
if [ ! -f "$NODE_PKG" ]; then
    wget https://nodejs.org/dist/v18.19.0/$NODE_PKG
fi

# 4. 创建离线安装说明
echo "[4/4] 创建说明文档..."
cat > $WORK_DIR/OFFLINE-README.md << 'EOF'
# LSF Dashboard 离线安装指南

## 文件结构
```
lsf-offline-package/
├── deploy/                    # 部署脚本和源码
├── python-deps/               # Python 依赖包
├── node-deps/                 # Node.js 安装包
└── OFFLINE-README.md          # 本文件
```

## 离线安装步骤

### 1. 复制所有文件到目标服务器

使用 U 盘、scp（跳板机）或其他方式将整个 `lsf-offline-package` 目录复制到目标服务器的 `/tmp/` 目录。

### 2. 安装系统依赖

目标服务器需要配置本地 yum 源或能访问基础包：

```bash
# 安装基础依赖
yum install -y python3 python3-pip git wget curl
```

### 3. 安装 Node.js

```bash
# 解压 Node.js
cd /tmp/lsf-offline-package/node-deps
tar -xf node-v18.19.0-linux-x64.tar.xz -C /usr/local/

# 创建软链接
ln -sf /usr/local/node-v18.19.0-linux-x64/bin/node /usr/bin/node
ln -sf /usr/local/node-v18.19.0-linux-x64/bin/npm /usr/bin/npm

# 验证
node -v
npm -v
```

### 4. 安装 Python 依赖

```bash
cd /tmp/lsf-offline-package/python-deps
pip3 install --no-index --find-links=. Flask Flask-CORS Werkzeug Jinja2 MarkupSafe itsdangerous click
```

### 5. 运行离线安装脚本

```bash
cd /tmp/lsf-offline-package/deploy

# 将 python-deps 和 node-deps 复制过来
cp -r ../python-deps ./
cp -r ../node-deps ./

chmod +x install-offline.sh
./install-offline.sh
```

### 6. 验证安装

```bash
# 检查服务状态
systemctl status lsf-dashboard

# 访问测试
curl http://localhost:5002/api/system-info
```

## 访问地址

安装完成后，浏览器访问：
```
http://服务器IP:5002
```
EOF

# 5. 打包
echo "[5/5] 打包离线包..."
cd /tmp
tar -czvf lsf-dashboard-offline-package.tar.gz lsf-offline-package/

echo ""
echo "========================================="
echo "  离线包制作完成!"
echo "========================================="
echo ""
echo "离线包位置：/tmp/lsf-dashboard-offline-package.tar.gz"
echo "大小：$(ls -lh /tmp/lsf-dashboard-offline-package.tar.gz | awk '{print $5}')"
echo ""
echo "使用方法:"
echo "  1. 将此文件复制到目标服务器"
echo "  2. 解压：tar -xzvf lsf-dashboard-offline-package.tar.gz"
echo "  3. 进入目录：cd lsf-offline-package"
echo "  4. 阅读说明：cat OFFLINE-README.md"
echo ""
