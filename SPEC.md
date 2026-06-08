# LSF 集群监控数据采集器 — SPEC.md

## 1. 项目概述

**项目名称**：`lsf-monitor`
**功能**：在 CentOS 7.9 LSF 集群节点机上，以每分钟为周期采集 `lsload` 和 `busers all` 命令的输出，存入 SQLite 数据库，并支持按小时/日/月统计节点负载趋势与用户 RUN 作业走势。
**目标用户**：HPC 集群运维/管理员

---

## 2. 数据源命令

### 2.1 `lsload`（节点负载）
```bash
lsload
```
典型输出字段（取前几列）：
```
HOST_NAME       type        total    swap    free    mem    ut     pg    io   ls    it   tmp    age   # Users
node001         Intel64     32768    8192    4096   8192   45.0   0.2   45   128  0.0   1024   30    12
node002         Intel64     32768    8192    4096   8192   82.3   1.1   12   256  0.0   2048   15    8
```
**采集字段**：`HOST_NAME`、`type`、`mem`、`ut`、`io`、`ls`、`it`、`# Users`

### 2.2 `busers all`（用户作业统计）
```bash
busers all
```
典型输出：
```
USER_NAME   GROUP_NAME   JOB_STATS   RUN    SSUSP    USUSP    RSV
user001     group_a       12/100      5      0        0        0
user002     group_b       8/50        3      1        0        0
```
**采集字段**：`USER_NAME`、`RUN`、`SSUSP`、`USUSP`、`RSV`

> **注意**：命令直接执行，不走 SSH。

---

## 3. 目录结构

```
lsf-monitor/
├── SPEC.md
├── requirements.txt          # Python 依赖
├── config.json               # 配置文件
├── collect.py                # 数据采集脚本（主程序）
├── db.py                     # 数据库操作
├── stats.py                  # 统计查询脚本
├── lsf-monitor.service       # systemd service 文件
└── run_collect.sh            # 独立运行脚本（无 systemd 时）
```

---

## 4. 数据库设计

**DB 文件**：`/var/lib/lsf-monitor/lsf_monitor.db`（可配置）

### 4.1 表 `lsload_snapshot`

| 字段        | 类型    | 说明                |
|------------|---------|-------------------|
| id         | INTEGER | 自增主键            |
| hostname   | TEXT    | 节点名              |
| type       | TEXT    | CPU 类型            |
| mem_total  | REAL    | 总内存（GB）         |
| mem_free   | REAL    | 空闲内存（GB）       |
| ut         | REAL    | CPU 利用率（%）      |
| io         | REAL    | IO 利用率（%）       |
| ls         | INTEGER | 负载（load scalar） |
| it         | REAL    | 空闲时间（分钟）      |
| num_users  | INTEGER | 当前用户数           |
| ts         | DATETIME| 采集时间（UTC）      |

**索引**：
- `(ts, hostname)` — 趋势查询
- `(hostname, ts)` — 单节点历史

### 4.2 表 `busers_snapshot`

| 字段       | 类型    | 说明            |
|-----------|---------|---------------|
| id        | INTEGER | 自增主键        |
| username  | TEXT    | 用户名          |
| run       | INTEGER | RUN 作业数      |
| ssusp     | INTEGER | SSUSP 作业数    |
| ususp     | INTEGER | USUSP 作业数    |
| rsv       | INTEGER | 预留作业数       |
| ts        | DATETIME| 采集时间（UTC）  |

**索引**：
- `(ts, username)`
- `(username, ts)`

---

## 5. 采集逻辑（collect.py）

### 5.1 采集周期
- **默认**：每 60 秒采集一次
- 可通过 `config.json` 配置 `interval`（秒）

### 5.2 执行方式
```bash
# lsload
lsload

# busers all
busers all
```
**不走 SSH，直接本地 `subprocess.Popen` 执行**。

### 5.3 健壮性
- 命令执行超时：10 秒
- 命令失败（返回码≠0）→ 记录错误日志 → 继续下次采集
- 解析失败 → 跳过该行，记录警告
- 首次启动：创建数据库及表结构（如不存在）

### 5.4 日志
- 日志文件：`/var/log/lsf-monitor/collect.log`（可配置）
- 日志级别：INFO（正常），WARNING（解析问题），ERROR（命令失败）
- 日志轮转：`collect.log` 单文件，最大 10MB，保留 5 份

---

## 6. 配置（config.json）

```json
{
  "db_path": "/var/lib/lsf-monitor/lsf_monitor.db",
  "log_path": "/var/log/lsf-monitor/collect.log",
  "interval": 60,
  "lsf_cmd_timeout": 10,
  "commands": {
    "lsload": ["lsload"],
    "busers": ["busers", "all"]
  }
}
```

---

## 7. 统计查询（stats.py）

支持三种时间粒度查询，输出 JSON 或 CSV：

### 7.1 节点 CPU 利用率趋势
```bash
python3 stats.py host-ut --hostname node001 --period hour --limit 24
```
输出：node001 过去 24 小时，每小时的平均/最大/最小 ut

### 7.2 用户 RUN 作业走势
```bash
python3 stats.py user-run --username user001 --period day --limit 30
```
输出：user001 过去 30 天，每天 RUN 作业数趋势

### 7.3 全局节点概览（当前时刻）
```bash
python3 stats.py overview
```
输出：所有节点当前 ut / mem_free / num_users 快照

### 7.4 聚合方式
| 粒度   | SQL 聚合函数       |
|--------|-----------------|
| hour   | AVG / MAX / MIN |
| day    | AVG / MAX / MIN |
| month  | AVG / MAX / MIN |

---

## 8. systemd Service

```ini
[Unit]
Description=LSF Monitor Data Collector
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/lsf-monitor/collect.py
Restart=always
RestartSec=10
User=lsfmon

[Install]
WantedBy=multi-user.target
```

> 以独立系统用户 `lsfmon` 运行（需手动创建），数据库和日志目录属主为 `lsfmon`。

---

## 9. 部署步骤

1. 创建系统用户 `lsfmon`
2. 创建目录 `/opt/lsf-monitor`（属主 `lsfmon`）、`/var/lib/lsf-monitor`、`/var/log/lsf-monitor`
3. 拷贝项目文件到 `/opt/lsf-monitor`
4. 安装依赖：`pip3 install -r requirements.txt`
5. 加载 systemd service：`cp lsf-monitor.service /etc/systemd/system/`
6. `systemctl daemon-reload && systemctl enable lsf-monitor && systemctl start lsf-monitor`

---

## 10. 依赖

```
# requirements.txt
DBUtils>=3.0.0
```

> 仅用 Python 标准库（`sqlite3`, `subprocess`, `logging`, `json`, `datetime`, `collections`）+ `DBUtils`（连接池，可选）。

---

## 11. 验收条件

- [ ] `collect.py` 能正确解析 `lsload` 输出，每 60 秒写入一条记录
- [ ] `collect.py` 能正确解析 `busers all` 输出，每 60 秒写入一条记录
- [ ] 命令执行超时/失败时不崩溃，记录 ERROR 日志后继续
- [ ] 数据库表/索引首次运行自动创建
- [ ] `stats.py overview` 输出当前所有节点快照
- [ ] `stats.py host-ut --hostname xxx --period hour` 输出小时聚合数据
- [ ] `stats.py user-run --username xxx --period day` 输出天聚合数据
- [ ] systemd service 能正常 start/restart
- [ ] 日志文件正常轮转
