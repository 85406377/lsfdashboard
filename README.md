# IBM LSF 作业监控 Dashboard
一个基于 Python + Vue + PyECharts 的 IBM LSF 作业监控系统。在LSF 主机或者节点机上运行，用系统用户和密码验证登录，用户可查看，管理个人的jobs。管理员admin可管理全部人员Jobs。 管理员帐号： 用户名: admin 密码: admin123
<img width="467" height="563" alt="1" src="https://github.com/user-attachments/assets/fefdb849-e002-44da-bdbe-3077126b680b" />
<img width="840" height="492" alt="2" src="https://github.com/user-attachments/assets/41db20a6-61d1-407b-a27c-23d78f208ce9" />
<img width="849" height="508" alt="3" src="https://github.com/user-attachments/assets/241d3351-b4de-4b45-9021-e673af0d3e7f" />
<img width="835" height="449" alt="4" src="https://github.com/user-attachments/assets/28492a51-2b64-41ed-a566-b73df35f42bf" />

## 功能特性

- 📊 **实时监控**: 作业、主机、负载、用户、队列信息
- 📈 **可视化图表**: 使用 PyECharts 生成负载趋势图
- 🔍 **作业详情**: 查看作业详细信息
- ⚔️ **作业管理**: 支持终止作业 (bkill)
- 🔄 **自动刷新**: 每 30 秒自动更新数据
- 📱 **响应式设计**: 适配各种屏幕尺寸

## 技术栈

### 后端
- Python 2.7.5 (兼容)
- Flask 1.1.4
- Flask-CORS

### 前端
- Vue 3
- Vue Router
- Pinia (状态管理)
- ECharts 5 (图表库)
- Axios
- Vite (构建工具)

## 项目结构

```
lsf-dashboard/
├── backend/
│   ├── app.py              # Flask 后端主程序
│   └── requirements.txt    # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue    # 主页面
│   │   │   └── JobDetail.vue    # 作业详情页
│   │   ├── store/
│   │   │   └── index.js         # 状态管理
│   │   ├── router/
│   │   │   └── index.js         # 路由配置
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── start.sh                # 启动脚本
└── README.md
```

## 安装步骤

### 1. 环境要求
- Python 2.7.5 或 Python 3.x
- Node.js 16+
- npm 或 yarn
- IBM LSF 环境 (需要 bjobs, bhosts, busers, bqueues, lsload 命令)

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 安装前端依赖并构建

```bash
cd ../frontend
npm install
npm run build
```

### 4. 启动服务

方式一：使用启动脚本
```bash
chmod +x start.sh
./start.sh
```

方式二：手动启动
```bash
# 启动后端 (端口 5000)
cd backend
python app.py

# 或者开发模式 (需要两个终端)
# 终端 1 - 后端
cd backend
python app.py

# 终端 2 - 前端开发服务器
cd frontend
npm run dev
```

## 访问地址

启动后访问：http://localhost:5000

开发模式访问：http://localhost:3000

## 页面说明

### 主页面 (Dashboard)

顶部显示:
- 用户名 + 主机名
- busers RUN 值
- 日期时间
- 操作系统版本
- 网络状态
- 刷新按钮

主要模块:
1. **作业列表**: 显示所有作业，可点击查看详情
2. **主机列表**: 显示计算节点状态
3. **系统负载**: 柱状图显示各主机负载
4. **用户列表**: 显示用户作业统计
5. **队列列表**: 显示队列状态
6. **负载趋势**: 折线图显示负载变化趋势

### 作业详情页

- 显示 `bjobs -l jobid` 的完整输出
- 提供 Kill 按钮终止作业
- 确认对话框防止误操作

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/system-info | GET | 获取系统信息 |
| /api/jobs | GET | 获取作业列表 |
| /api/hosts | GET | 获取主机列表 |
| /api/users | GET | 获取用户列表 |
| /api/queues | GET | 获取队列列表 |
| /api/load | GET | 获取负载信息 |
| /api/load-trend | GET | 获取负载趋势 |
| /api/job/<job_id> | GET | 获取作业详情 |
| /api/kill/<job_id> | POST | 终止作业 |

## 自定义配置

### 修改端口

编辑 `backend/app.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

### 修改刷新间隔

编辑 `frontend/src/views/Dashboard.vue`:
```javascript
setInterval(async () => {
  // ...
}, 30000)  // 30 秒，单位毫秒
```

## 注意事项

1. **LSF 环境**: 确保系统已安装 IBM LSF 并配置好环境变量
2. **权限**: 确保运行用户有权限执行 LSF 命令
3. **Python 2.7**: 虽然代码兼容 2.7.5，但建议使用 Python 3.x
4. **安全**: 生产环境请关闭 debug 模式，添加认证机制

## 故障排除

### 命令执行失败
检查 LSF 环境是否正确配置:
```bash
which bjobs
which bhosts
bjobs -V
```

### 前端构建失败
清除 node_modules 重新安装:
```bash
rm -rf node_modules package-lock.json
npm install
```

### 端口被占用
修改 `backend/app.py` 中的端口号

## 扩展功能建议

- [ ] 添加用户认证
- [ ] 添加作业提交功能
- [ ] 添加邮件/消息通知
- [ ] 添加历史数据持久化
- [ ] 添加更多图表类型
- [ ] 支持多集群监控

##离线安装：
- [ ]创建了新的离线安装包lsf-dashboard-offline-package.tar.gz（48MB）
- [ ]将安装包和更新的中文安装说明文档部署到工作区
- [ ]安装包已包含：
- [ ]所有必要的Python依赖包（Flask、Flask-CORS等）
- [ ]Node.js 18.x运行时环境
- [ ]完整的部署脚本和文档
- [ ]支持离线安装和在线安装两种方式
- [ ]您可以在目标服务器上通过以下步骤安装：
- [ ]将安装包复制到目标服务器
- [ ]解压安装包并运行./install-offline.sh
- [ ]访问服务器IP:5002查看Dashboard

## License

MIT License

## Author

Created for IBM LSF monitoring and visualization.
