#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web.py — LSF Monitor Flask Web 界面
在 CentOS 上运行，Windows 浏览器访问 http://<CentOS-IP>:5000
"""

import os
import sys
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, request, jsonify, Response

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

try:
    from db import Database
except ImportError:
    Database = None

# ──────────────────────────────────────────────
#  Config
# ──────────────────────────────────────────────

CONFIG_PATH = BASE_DIR / "config.json"
PID_FILE    = BASE_DIR / "collect.pid"

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)

config = load_config()
DB_PATH = config.get("db_path", str(BASE_DIR / "lsf_monitor.db"))

# ──────────────────────────────────────────────
#  Flask app
# ──────────────────────────────────────────────

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))


# ──────────────────────────────────────────────
#  Process helpers
# ──────────────────────────────────────────────

def get_pid():
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def is_running():
    pid = get_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_collect():
    if is_running():
        return "already running"
    log_file = config.get("log_path", str(BASE_DIR / "collect.log"))
    log_dir  = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    with open(os.devnull, "w") as devnull:
        proc = subprocess.Popen(
            [sys.executable, str(BASE_DIR / "collect.py")],
            stdout=devnull, stderr=devnull,
        )
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    return "started"


def stop_collect():
    pid = get_pid()
    if pid is None:
        return "not running"
    try:
        os.kill(pid, 15)   # SIGTERM
    except OSError:
        pass
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    return "stopped"


# ──────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html",
        running=is_running(),
        db_path=DB_PATH,
    )


@app.route("/api/status")
def api_status():
    return jsonify({"running": is_running(), "pid": get_pid()})


@app.route("/api/start", methods=["POST"])
def api_start():
    msg = start_collect()
    return jsonify({"ok": True, "msg": msg})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    msg = stop_collect()
    return jsonify({"ok": True, "msg": msg})


@app.route("/api/overview")
def api_overview():
    if Database is None:
        return jsonify({"error": "db module not available"}), 500
    try:
        db = Database(DB_PATH)
        hosts = db.query_overview()
        users = db.query_user_overview()
        return jsonify({"hosts": hosts, "users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/host_ut")
def api_host_ut():
    if Database is None:
        return jsonify({"error": "db module not available"}), 500
    hostname = request.args.get("hostname", "")
    period   = request.args.get("period", "hour")
    limit    = int(request.args.get("limit", 24))
    ts_end   = datetime.now(timezone.utc)
    if period == "hour":
        ts_start = ts_end - timedelta(hours=limit)
    elif period == "day":
        ts_start = ts_end - timedelta(days=limit)
    else:
        ts_start = ts_end - timedelta(days=limit * 30)
    try:
        db = Database(DB_PATH)
        rows = db.query_host_ut(hostname, period, limit, ts_start, ts_end)
        return jsonify({"rows": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/user_run")
def api_user_run():
    if Database is None:
        return jsonify({"error": "db module not available"}), 500
    username = request.args.get("username", "")
    period   = request.args.get("period", "day")
    limit    = int(request.args.get("limit", 30))
    ts_end   = datetime.now(timezone.utc)
    if period == "hour":
        ts_start = ts_end - timedelta(hours=limit)
    elif period == "day":
        ts_start = ts_end - timedelta(days=limit)
    else:
        ts_start = ts_end - timedelta(days=limit * 30)
    try:
        db = Database(DB_PATH)
        rows = db.query_user_run(username, period, limit, ts_start, ts_end)
        return jsonify({"rows": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/hosts")
def api_hosts():
    """返回所有已采集的主机名列表（去重）"""
    if Database is None:
        return jsonify([])
    try:
        db = Database(DB_PATH)
        conn = db._conn()
        try:
            cur = conn.execute(
                "SELECT DISTINCT hostname FROM lsload_snapshot ORDER BY hostname"
            )
            return jsonify([r[0] for r in cur.fetchall()])
        finally:
            db._close_conn(conn)
    except Exception:
        return jsonify([])


@app.route("/api/users")
def api_users():
    """返回所有已采集的用户名列表（去重）"""
    if Database is None:
        return jsonify([])
    try:
        db = Database(DB_PATH)
        conn = db._conn()
        try:
            cur = conn.execute(
                "SELECT DISTINCT username FROM busers_snapshot ORDER BY username"
            )
            return jsonify([r[0] for r in cur.fetchall()])
        finally:
            db._close_conn(conn)
    except Exception:
        return jsonify([])


# ──────────────────────────────────────────────
#  Run
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # 允许局域网访问
    app.run(host="0.0.0.0", port=5000, debug=False)
