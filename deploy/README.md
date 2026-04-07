# LSF Dashboard 部署包说明

## 文件说明

```
deploy/
├── install.sh              # 在线一键安装脚本（推荐）
├── install-offline.sh      # 离线安装脚本
├── lsf-dashboard-src.tar.gz  # 源码包
└── README.md               # 本文件
```

## 快速部署（推荐）

### 方式一：在线安装（目标服务器可上网）

1. 将整个 `deploy` 目录复制到目标服务器：
```bash
# 在源服务器上打包
cd /root/.openclaw/workspace/lsf-dashboard
tar -czvf lsf-dashboard-deploy.tar.gz deploy/

# 使用 scp 复制
scp lsf-dashboard-deploy.tar.gz root@目标服务器 IP:/tmp/

# 在目标服务器上解压
cd /tmp
tar -xzvf lsf-dashboard-deploy.tar.gz
cd deploy
```

2. 执行安装脚本：
```bash
chmod +x install.sh
./install.sh
```

3. 访问 Dashboard：
```
http://目标服务器 IP:5002
```

### 方式二：离线安装（目标服务器无法上网）

需要在有网络的机器上准备离线包：

#### 步骤 1：准备离线依赖包

```bash
# 创建离线包目录
mkdir -p /tmp/lsf-offline/{python-deps,node-deps}

# 下载 Python 依赖
cd /tmp/lsf-offline/python-deps
pip3 download Flask Flask-CORS -d .

# 下载 Node.js (如果需要)
cd /tmp/lsf-offline/node-deps
wget https://nodejs.org/dist/v18.19.0/node-v18.19.0-linux-x64.tar.xz

# 打包
cd /tmp/lsf-offline
tar -czvf lsf-offline-deps.tar.gz .
```

#### 步骤 2：在目标服务器上安装

```bash
# 复制所有文件到目标服务器
scp -r deploy/ root@目标服务器 IP:/tmp/
scp lsf-offline-deps.tar.gz root@目标服务器 IP:/tmp/

# 在目标服务器上
cd /tmp
tar -xzvf lsf-offline-deps.tar.gz

# 安装系统依赖（需要配置本地 yum 源）
yum install -y python3 python3-pip nodejs npm

# 安装 Python 离线包
pip3 install --no-index --find-links=/tmp/lsf-offline/python-deps/ Flask Flask-CORS

# 运行离线安装脚本
cd deploy
chmod +x install-offline.sh
./install-offline.sh
```

## 手动部署

如果自动脚本无法运行，可以手动部署：

### 1. 安装系统依赖

```bash
# 配置 EPEL 源
yum install -y epel-release

# 安装依赖
yum install -y python3 python3-pip nodejs npm git
```

### 2. 升级 Node.js（如果需要）

```bash
# 安装 Node.js 18
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs
```

### 3. 安装应用

```bash
# 解压源码
tar -xzf lsf-dashboard-src.tar.gz -C /opt/
cd /opt/lsf-dashboard

# 安装 Python 依赖
cd backend
pip3 install -r requirements.txt

# 构建前端
cd ../frontend
npm install
npm run build
```

### 4. 配置服务

```bash
# 创建 systemd 服务
cat > /etc/systemd/system/lsf-dashboard.service << 'EOF'
[Unit]
Description=IBM LSF Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/lsf-dashboard/backend
ExecStart=/usr/bin/python3 /opt/lsf-dashboard/backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable lsf-dashboard
systemctl start lsf-dashboard
```

### 5. 配置防火墙

```bash
firewall-cmd --permanent --add-port=5002/tcp
firewall-cmd --reload
```

## 验证安装

```bash
# 检查服务状态
systemctl status lsf-dashboard

# 查看日志
journalctl -u lsf-dashboard -f

# 测试 API
curl http://localhost:5002/api/system-info

# 测试网页
curl http://localhost:5002
```

## 常见问题

### 1. 端口被占用

修改 `backend/app.py` 中的端口号：
```python
app.run(host='0.0.0.0', port=5002, debug=True)
```

### 2. Node.js 版本过低

```bash
# 卸载旧版本
yum remove nodejs npm

# 安装新版本
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs
```

### 3. Python 依赖安装失败

```bash
# 升级 pip
pip3 install --upgrade pip

# 使用国内镜像
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 前端构建失败

```bash
# 清理缓存
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force

# 重新安装
npm install
npm run build
```

### 5. LSF 命令不存在

这是正常的，如果没有安装 IBM LSF 软件，页面会显示"暂无数据"。
如需测试，可以安装 LSF 或修改代码使用模拟数据。

## 卸载

```bash
# 停止服务
systemctl stop lsf-dashboard
systemctl disable lsf-dashboard

# 删除服务文件
rm /etc/systemd/system/lsf-dashboard.service
systemctl daemon-reload

# 删除安装目录
rm -rf /opt/lsf-dashboard

# 关闭防火墙端口
firewall-cmd --permanent --remove-port=5002/tcp
firewall-cmd --reload
```

## 技术支持

如有问题，请检查：
1. 系统日志：`journalctl -u lsf-dashboard -f`
2. 应用日志：`/tmp/lsf-dashboard.log`
3. 防火墙状态：`systemctl status firewalld`
4. 服务状态：`systemctl status lsf-dashboard`
