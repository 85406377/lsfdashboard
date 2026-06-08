# LSF Dashboard

**LSF Cluster Monitoring & Data Collector**

Collects `lsload` and `busers all` output from LSF cluster nodes every minute, stores it in SQLite, and visualizes node load trends and user job statistics via a Flask-powered web dashboard.

> Designed for **CentOS 7.9 + LSF 10+**. Commands run locally — no SSH required.

---

## Features

- **Automatic data collection** — every 60 s (configurable), directly via `subprocess`
- **No SSH dependency** — runs on each node; nodes only need Python 3
- **SQLite persistence** — lightweight, WAL-mode, concurrent-read safe
- **Web dashboard** — Flask + ECharts, four tabs:
  - *Overview* — global CPU, r1m, RUN jobs, node status
  - *Node Trend* — per-node UT%, load, memory, swap
  - *User Trend* — per-user RUN/PEND jobs over time
  - *Daily Report* — daily aggregated stats + top-10 user table
- **Flexible X-axis** — hourly periods show `HH:mm`; day/month periods show `MM-DD` at midnight
- **systemd service** included — runs as dedicated `lsfmon` user, auto-restarts on failure
- **Log rotation** — 10 MB max, 5 generations kept

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Node A / Node B / Node C / ... (each runs)          │
│                                                      │
│  ┌──────────────┐   ┌──────────────┐               │
│  │  collect.py  │   │ dashboard.py │               │
│  │  (daemon)     │   │ (Flask :5000) │               │
│  └──────────────┘   └──────────────┘               │
│        ↓                     ↑                       │
│  ┌──────────────┐   ┌──────────────┐               │
│  │  SQLite DB   │   │   Browser    │               │
│  │  lsf_mon.db  │←───│  Dashboard   │               │
│  └──────────────┘   └──────────────┘               │
└─────────────────────────────────────────────────────┘
```

Each node runs its own `collect.py` daemon writing to a shared SQLite file (NFS mount recommended) or local DB.

---

## File Structure

```
lsf-monitor/
├── SPEC.md                 # Full technical specification
├── README.md               # This file
├── requirements.txt       # Python dependencies
├── config.json            # Runtime configuration
├── collect.py             # Data collection daemon
├── dashboard.py           # Flask web dashboard
├── db.py                  # Database operations
├── gui.py                 # Optional standalone GUI
├── web.py                 # Lightweight web server wrapper
├── deploy.sh              # One-shot deployment script
├── lsf-monitor.service    # systemd unit file
├── run_collect.sh         # Non-systemd process supervisor
├── static/                # ECharts JS bundle
│   └── echarts.min.js
└── templates/             # HTML templates
    ├── dashboard.html     # Main dashboard (4 tabs)
    ├── index.html        # Alternative entry point
    └── debug.html        # Debug page
```

---

## Requirements

- **OS**: CentOS 7.9 (or compatible RHEL-based LSF node)
- **Python**: 3.6+
- **LSF**: 10.0+ (commands `lsload`, `busers` available in PATH)
- **Python packages**: see `requirements.txt`

```
DBUtils>=3.0.0
```

All other dependencies are Python standard library only (`sqlite3`, `subprocess`, `logging`, `json`, `datetime`, `collections`, `flask`, `pyecharts`).

---

## Installation

### 1. Prepare the system user and directories

```bash
# Run as root on the LSF node
sudo useradd -r -s /sbin/nologin lsfmon

sudo mkdir -p /opt/lsf-monitor
sudo mkdir -p /var/lib/lsf-monitor
sudo mkdir -p /var/log/lsf-monitor

sudo chown -R lsfmon:lsfmon /opt/lsf-monitor
sudo chown -R lsfmon:lsfmon /var/lib/lsf-monitor
sudo chown -R lsfmon:lsfmon /var/log/lsf-monitor
```

### 2. Copy files

```bash
# From your build machine
scp -r lsf-monitor/ root@<node>:/opt/lsf-monitor/
```

### 3. Install Python dependencies

```bash
sudo pip3 install -r /opt/lsf-monitor/requirements.txt
```

### 4. Configure (optional)

Edit `/opt/lsf-monitor/config.json`:

```json
{
  "db_path": "/var/lib/lsf-monitor/lsf_monitor.db",
  "log_path": "/var/log/lsf-monitor/collect.log",
  "interval": 60,
  "lsf_cmd_timeout": 10,
  "dashboard_port": 5000,
  "listen": "0.0.0.0",
  "commands": {
    "lsload": ["lsload"],
    "busers": ["busers", "all"]
  }
}
```

### 5. Start via systemd

```bash
sudo cp /opt/lsf-monitor/lsf-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lsf-monitor
sudo systemctl start lsf-monitor
```

### Or start without systemd

```bash
sudo -u lsfmon bash /opt/lsf-monitor/run_collect.sh start
```

---

## Dashboard

Access at `http://<node-ip>:5000` (default port `5000`, configurable).

### Tab: Overview
Global view — average UT% of all nodes, average r1m, total RUN jobs across all users, and a pie chart of node status breakdown.

### Tab: Node Trend
Select a hostname from the dropdown to see that node's:
- **CPU Load** — r1m & r15m line chart
- **UT% & Running Tasks** — UT% and load scalar (ls)
- **Memory & Swap** — in GB
- **Hourly UT%** — bar chart
- **CPU / Memory rings** — donut charts of current utilization

### Tab: User Trend
Select a username to see:
- **RUN & PEND Jobs** — line chart over time
- **Max RUN by Day** — bar chart (day-level aggregation)
- **Peak RUN** — top 30 users bar chart

### Tab: Daily Report
- **Avg UT% by Day** — line chart
- **Max r15m by Day** — line chart
- **Busy Ratio** — percentage of samples where r15m > 4
- **Top 10 Users by Peak RUN** — bar chart + table

### Period Selector
All charts respect the **Period** dropdown:

| Period | X-axis format |
|--------|--------------|
| `1h`, `24h` | `HH:mm` — hour:minute timestamps |
| `7d`, `30d` | `MM-DD` at midnight only — keeps the axis clean |

---

## API Reference

All endpoints return JSON.

### Lists

```
GET /api/hosts       → ["node001", "node002", ...]
GET /api/users      → ["user001", "user002", ...]
```

### Node data

```
GET /api/host_ts/<hostname>?fields=r1m,r15m,ut,ls,mem&period=24h
GET /api/host_agg/<hostname>?period=24h
GET /api/overview_ut?period=24h&hostname=node001
GET /api/overview_r1m?period=24h
GET /api/host_status?period=24h
GET /api/host_ring/<hostname>?period=24h
```

### User data

```
GET /api/user_agg/<username>?period=24h
GET /api/user_quota?period=30d
GET /api/overview_run?period=24h
```

### Daily aggregates

```
GET /api/daily_node?period=30d
GET /api/daily_user?period=30d
```

---

## Database Schema

**File**: `/var/lib/lsf-monitor/lsf_monitor.db` (SQLite, WAL mode)

### `lsload_snapshot`

| Column     | Type    | Description                    |
|-----------|---------|-------------------------------|
| id         | INTEGER | Primary key (auto-increment)  |
| hostname   | TEXT    | Node name                     |
| type       | TEXT    | CPU type                      |
| mem_total  | REAL    | Total memory (GB)             |
| mem_free   | REAL    | Free memory (GB)              |
| ut         | REAL    | CPU utilization (%)           |
| io         | REAL    | IO utilization (%)            |
| ls         | INTEGER | Load scalar                   |
| it         | REAL    | Idle time (minutes)           |
| num_users  | INTEGER | Number of active users         |
| ts         | TEXT    | Timestamp (ISO 8601 UTC)       |

Indexes: `(ts, hostname)`, `(hostname, ts)`

### `busers_snapshot`

| Column    | Type    | Description            |
|----------|---------|------------------------|
| id       | INTEGER | Primary key            |
| username | TEXT    | User name              |
| run      | INTEGER | Running jobs           |
| ssusp    | INTEGER | SSUSP jobs             |
| ususp    | INTEGER | USUSP jobs             |
| rsv      | INTEGER | Reserved jobs          |
| ts       | TEXT    | Timestamp (ISO 8601 UTC) |

Indexes: `(ts, username)`, `(username, ts)`

---

## Data Retention

Delete records older than 90 days to save space:

```bash
sqlite3 /var/lib/lsf-monitor/lsf_monitor.db \
  "DELETE FROM lsload_snapshot WHERE ts < datetime('now', '-90 days');" \
  "DELETE FROM busers_snapshot WHERE ts < datetime('now', '-90 days');" \
  "VACUUM;"
```

---

## Troubleshooting

**collect.py exits immediately with no output**

Check that LSF commands are in PATH:
```bash
which lsload busers
lsload   # should print the load table
```

**Dashboard shows "no data"**

Verify the DB file exists and is non-empty:
```bash
ls -lh /var/lib/lsf-monitor/lsf_monitor.db
sqlite3 /var/lib/lsf-monitor/lsf_monitor.db "SELECT COUNT(*) FROM lsload_snapshot;"
```

**Permission denied on log file**

Ensure the log directory is owned by `lsfmon`:
```bash
sudo chown -R lsfmon:lsfmon /var/log/lsf-monitor
```

**systemd service won't start**

Check the journal:
```bash
sudo journalctl -u lsf-monitor -n 50 --no-pager
```

**Dashboard accessible but charts empty**

The browser may be serving a cached `dashboard.html`. Hard-refresh (`Ctrl+Shift+R`) or disable cache in DevTools.

---

## License

Internal use only. Built for HPC cluster operations.