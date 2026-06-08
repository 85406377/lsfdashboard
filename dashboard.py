#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard.py — LSF Monitor Flask Dashboard
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify
from pyecharts import options as opts
from pyecharts import globals

# ── Setup ──────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────

CONFIG_PATH = BASE_DIR / "config.json"

def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"db_path": str(BASE_DIR / "lsf_monitor.db")}

config  = load_config()
DB_PATH = config.get("db_path", str(BASE_DIR / "lsf_monitor.db"))
PORT    = int(config.get("dashboard_port", 5000))
LISTEN  = config.get("listen", "0.0.0.0")

# ── Database ────────────────────────────────────────────────────────────────

import sqlite3

class DashboardDB:
    def __init__(self, db_path):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=60,
                               isolation_level=None,
                               check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 60000")
        return conn

    def _close(self, conn):
        try:
            conn.close()
        except Exception:
            pass

    @staticmethod
    def _strftime(ts):
        return ts.strftime("%Y-%m-%d %H:%M:%S")

    def _rows(self, cur):
        rows = [dict(r) for r in cur.fetchall()]
        for row in rows:
            for k, v in row.items():
                if isinstance(v, float):
                    row[k] = round(v, 2)
        return rows

    # ── lists ─────────────────────────────────────────────────────────────

    def list_hosts(self):
        conn = self._conn()
        try:
            cur = conn.execute(
                "SELECT DISTINCT hostname FROM lsload_snapshot ORDER BY hostname")
            return [r[0] for r in cur.fetchall()]
        finally:
            self._close(conn)

    def list_users(self):
        conn = self._conn()
        try:
            cur = conn.execute(
                "SELECT DISTINCT username FROM busers_snapshot ORDER BY username")
            return [r[0] for r in cur.fetchall()]
        finally:
            self._close(conn)

    # ── host raw ts ──────────────────────────────────────────────────────

    def host_ts(self, hostname, fields, ts_start, ts_end):
        cols = ", ".join(fields)
        sql = (
            f"SELECT ts, {cols} FROM lsload_snapshot "
            f"WHERE hostname = ? AND ts >= ? AND ts <= ? "
            f"ORDER BY ts ASC LIMIT 5000"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (hostname, self._strftime(ts_start),
                                       self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    # ── host aggregated ──────────────────────────────────────────────────

    def host_agg(self, hostname, bucket_fn, fields, ts_start, ts_end, limit=200):
        select_parts = [f"strftime('%Y-%m-%d %H:00:00', ts) AS bucket"]
        select_parts += [f"{agg} AS {name}" for name, agg in fields]
        select_sql   = ", ".join(select_parts)
        sql = (
            f"SELECT {select_sql} "
            f"FROM lsload_snapshot "
            f"WHERE hostname = ? AND ts >= ? AND ts <= ? "
            f"GROUP BY strftime('%Y-%m-%d %H:00:00', ts) "
            f"ORDER BY strftime('%Y-%m-%d %H:00:00', ts) ASC LIMIT {limit}"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (hostname, self._strftime(ts_start),
                                       self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    # ── user aggregated ──────────────────────────────────────────────────

    def user_agg(self, username, bucket_fn, fields, ts_start, ts_end, limit=200):
        select_parts = [f"strftime('%Y-%m-%d %H:00:00', ts) AS bucket"]
        select_parts += [f"{agg} AS {name}" for name, agg in fields]
        select_sql   = ", ".join(select_parts)
        sql = (
            f"SELECT {select_sql} "
            f"FROM busers_snapshot "
            f"WHERE username = ? AND ts >= ? AND ts <= ? "
            f"GROUP BY strftime('%Y-%m-%d %H:00:00', ts) "
            f"ORDER BY strftime('%Y-%m-%d %H:00:00', ts) ASC LIMIT {limit}"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (username, self._strftime(ts_start),
                                       self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    # ── overview ─────────────────────────────────────────────────────────

    def overview_ut(self, ts_start, ts_end, hostname=None):
        if hostname:
            sql = (
                "SELECT strftime('%Y-%m-%d %H:00:00', ts) AS bucket, "
                "ROUND(AVG(ut), 2) AS avg_ut "
                "FROM lsload_snapshot "
                "WHERE hostname = ? AND ts >= ? AND ts <= ? "
                "GROUP BY strftime('%Y-%m-%d %H:00:00', ts) "
                "ORDER BY strftime('%Y-%m-%d %H:00:00', ts) ASC LIMIT 200"
            )
            conn = self._conn()
            try:
                cur = conn.execute(sql, (hostname, self._strftime(ts_start), self._strftime(ts_end)))
                return self._rows(cur)
            finally:
                self._close(conn)
        sql = (
            "SELECT strftime('%Y-%m-%d %H:00:00', ts) AS bucket, "
            "ROUND(AVG(ut), 2) AS avg_ut "
            "FROM lsload_snapshot "
            "WHERE ts >= ? AND ts <= ? "
            "GROUP BY strftime('%Y-%m-%d %H:00:00', ts) "
            "ORDER BY strftime('%Y-%m-%d %H:00:00', ts) ASC LIMIT 200"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (self._strftime(ts_start), self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    def overview_r1m(self, ts_start, ts_end, hostname=None):
        if hostname:
            sql = (
                "SELECT strftime('%Y-%m-%d %H:00:00', ts) AS bucket, "
                "ROUND(AVG(r1m), 2) AS avg_r1m "
                "FROM lsload_snapshot "
                "WHERE hostname = ? AND ts >= ? AND ts <= ? "
                "GROUP BY strftime('%Y-%m-%d %H:00:00', ts) "
                "ORDER BY strftime('%Y-%m-%d %H:00:00', ts) ASC LIMIT 200"
            )
            conn = self._conn()
            try:
                cur = conn.execute(sql, (hostname, self._strftime(ts_start), self._strftime(ts_end)))
                return self._rows(cur)
            finally:
                self._close(conn)
        sql = (
            "SELECT strftime('%Y-%m-%d %H:00:00', ts) AS bucket, "
            "ROUND(AVG(r1m), 2) AS avg_r1m "
            "FROM lsload_snapshot "
            "WHERE ts >= ? AND ts <= ? "
            "GROUP BY strftime('%Y-%m-%d %H:00:00', ts) "
            "ORDER BY strftime('%Y-%m-%d %H:00:00', ts) ASC LIMIT 200"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (self._strftime(ts_start), self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    def overview_run(self, ts_start, ts_end, hostname=None):
        # busers_snapshot has no hostname column (user-level data only)
        # hostname param is accepted for API compatibility but ignored here
        sql = (
            "SELECT strftime('%Y-%m-%d %H:00:00', ts) AS bucket, "
            "SUM(run) AS total_run "
            "FROM busers_snapshot "
            "WHERE ts >= ? AND ts <= ? "
            "GROUP BY strftime('%Y-%m-%d %H:00:00', ts) "
            "ORDER BY strftime('%Y-%m-%d %H:00:00', ts) ASC LIMIT 200"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (self._strftime(ts_start), self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    def host_status_summary(self, ts_start, ts_end, hostname=None):
        if hostname:
            sql = (
                "SELECT status, COUNT(*) AS cnt "
                "FROM lsload_snapshot "
                "WHERE hostname = ? AND ts >= ? AND ts <= ? "
                "GROUP BY status"
            )
            conn = self._conn()
            try:
                cur = conn.execute(sql, (hostname, self._strftime(ts_start), self._strftime(ts_end)))
                return self._rows(cur)
            finally:
                self._close(conn)
        sql = (
            "SELECT status, COUNT(*) AS cnt "
            "FROM lsload_snapshot "
            "WHERE ts >= ? AND ts <= ? "
            "GROUP BY status"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (self._strftime(ts_start), self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    # ── daily summaries ──────────────────────────────────────────────────

    def daily_node_summary(self, ts_start, ts_end):
        sql = (
            "SELECT "
            "  strftime('%Y-%m-%d', ts) AS day,"
            "  AVG(ut)    AS avg_ut,"
            "  MAX(r15m)  AS max_r15m,"
            "  AVG(r1m)   AS avg_r1m,"
            "  COUNT(*)   AS samples,"
            "  SUM(CASE WHEN r15m > 4 THEN 1 ELSE 0 END) AS busy_samples "
            "FROM lsload_snapshot "
            "WHERE ts >= ? AND ts <= ? "
            "GROUP BY day ORDER BY day ASC LIMIT 90"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (self._strftime(ts_start), self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    def daily_user_summary(self, ts_start, ts_end):
        sql = (
            "SELECT "
            "  strftime('%Y-%m-%d', ts) AS day,"
            "  username,"
            "  MAX(run) AS max_run,"
            "  AVG(run) AS avg_run,"
            "  SUM(CASE WHEN pend > 0 THEN pend ELSE 0 END) AS total_pend "
            "FROM busers_snapshot "
            "WHERE ts >= ? AND ts <= ? "
            "GROUP BY day, username ORDER BY day ASC, max_run DESC LIMIT 500"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (self._strftime(ts_start), self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)

    def user_quota_stats(self, ts_start, ts_end):
        sql = (
            "SELECT username, MAX(run) AS peak_run "
            "FROM busers_snapshot "
            "WHERE ts >= ? AND ts <= ? "
            "GROUP BY username ORDER BY peak_run DESC"
        )
        conn = self._conn()
        try:
            cur = conn.execute(sql, (self._strftime(ts_start), self._strftime(ts_end)))
            return self._rows(cur)
        finally:
            self._close(conn)


db = DashboardDB(DB_PATH)

# ── Flask App ───────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder="templates")
app.config["JSON_AS_ASCII"] = False

# Force no-cache on ALL responses to prevent browser caching issues
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Log ALL incoming requests
@app.before_request
def log_request():
    logger.info(f"REQUEST: {request.method} {request.url}")

# Track 404s so we know what's missing
@app.errorhandler(404)
def log_404(e):
    logger.warning(f"404 NOT FOUND: {request.method} {request.url} — {str(e)}")
    from flask import make_response
    return make_response(jsonify({"error": "not_found", "url": request.url}), 404)

# ── Period helper ────────────────────────────────────────────────────────────

def parse_period(period):
    now = datetime.now()
    p   = period.lower()
    if p == "1h":
        return now - timedelta(hours=1), now
    if p == "24h":
        return now - timedelta(hours=24), now
    if p == "7d":
        return now - timedelta(days=7), now
    if p == "30d":
        return now - timedelta(days=30), now
    return now - timedelta(hours=24), now

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    from flask import send_from_directory
    return send_from_directory("templates", "dashboard.html")

@app.route("/test")
def test_page():
    from flask import send_from_directory
    return send_from_directory("templates", "test.html")

@app.route("/debug")
def debug_page():
    from flask import send_from_directory
    return send_from_directory("templates", "debug.html")

@app.route("/index")
def index2_page():
    from flask import send_from_directory
    return send_from_directory("templates", "index.html")

# ── List APIs ────────────────────────────────────────────────────────────────

@app.route("/api/hosts")
def api_hosts():
    return jsonify(db.list_hosts())

@app.route("/api/users")
def api_users():
    return jsonify(db.list_users())

# ── Host APIs ────────────────────────────────────────────────────────────────

@app.route("/api/host_ts/<hostname>")
def api_host_ts(hostname):
    fields_str = request.args.get("fields", "r1m,r15m,ut,ls,mem,swp")
    fields     = [f.strip() for f in fields_str.split(",") if f.strip()]
    period     = request.args.get("period", "24h")
    ts_start, ts_end = parse_period(period)
    rows = db.host_ts(hostname, fields, ts_start, ts_end)
    return jsonify(rows)

@app.route("/api/host_agg/<hostname>")
def api_host_agg(hostname):
    period     = request.args.get("period", "24h")
    ts_start, ts_end = parse_period(period)
    fields = [
        ("avg_ut",  "AVG(ut)"),
        ("avg_r1m", "AVG(r1m)"),
        ("avg_r15m","AVG(r15m)"),
        ("avg_ls",  "AVG(ls)"),
        ("avg_mem", "AVG(mem)"),
        ("avg_swp", "AVG(swp)"),
    ]
    rows = db.host_agg(hostname, None, fields, ts_start, ts_end)
    return jsonify(rows)

# ── User APIs ────────────────────────────────────────────────────────────────

@app.route("/api/user_agg/<username>")
def api_user_agg(username):
    period     = request.args.get("period", "24h")
    ts_start, ts_end = parse_period(period)
    fields = [
        ("avg_run",  "AVG(run)"),
        ("avg_pend", "AVG(pend)"),
        ("max_run",  "MAX(run)"),
    ]
    rows = db.user_agg(username, None, fields, ts_start, ts_end)
    return jsonify(rows)

@app.route("/api/user_quota")
def api_user_quota():
    period     = request.args.get("period", "30d")
    ts_start, ts_end = parse_period(period)
    return jsonify(db.user_quota_stats(ts_start, ts_end))

# ── Overview APIs ────────────────────────────────────────────────────────────

@app.route("/api/overview_ut")
def api_overview_ut():
    period     = request.args.get("period", "24h")
    hostname   = request.args.get("hostname", "") or None
    ts_start, ts_end = parse_period(period)
    return jsonify(db.overview_ut(ts_start, ts_end, hostname))

@app.route("/api/overview_r1m")
def api_overview_r1m():
    period     = request.args.get("period", "24h")
    hostname   = request.args.get("hostname", "") or None
    ts_start, ts_end = parse_period(period)
    return jsonify(db.overview_r1m(ts_start, ts_end, hostname))

@app.route("/api/overview_run")
def api_overview_run():
    period     = request.args.get("period", "24h")
    hostname   = request.args.get("hostname", "") or None
    ts_start, ts_end = parse_period(period)
    return jsonify(db.overview_run(ts_start, ts_end, hostname))

@app.route("/api/host_status")
def api_host_status():
    period     = request.args.get("period", "24h")
    hostname   = request.args.get("hostname", "") or None
    ts_start, ts_end = parse_period(period)
    return jsonify(db.host_status_summary(ts_start, ts_end, hostname))

@app.route("/api/overview_cpu_ring")
def api_overview_cpu_ring():
    """Return avg CPU used% and free% for the current period."""
    period     = request.args.get("period", "24h")
    ts_start, ts_end = parse_period(period)
    rows = db.overview_ut(ts_start, ts_end)
    if not rows:
        return jsonify({"cpu_used": 0, "cpu_free": 100})
    vals = [r["avg_ut"] for r in rows if r.get("avg_ut") is not None]
    if not vals:
        return jsonify({"cpu_used": 0, "cpu_free": 100})
    avg_used = round(sum(vals) / len(vals), 2)
    return jsonify({"cpu_used": avg_used, "cpu_free": round(100 - avg_used, 2)})

@app.route("/api/host_ring/<hostname>")
def api_host_ring(hostname):
    """Return avg UT%, mem, swp for a specific host to render ring charts."""
    period     = request.args.get("period", "24h")
    ts_start, ts_end = parse_period(period)
    fields = [
        ("avg_ut",  "AVG(ut)"),
        ("avg_mem", "AVG(mem)"),
        ("avg_swp", "AVG(swp)"),
    ]
    rows = db.host_agg(hostname, None, fields, ts_start, ts_end, limit=1)
    if not rows:
        return jsonify({"cpu_used": 0, "cpu_free": 100, "mem_avg": 0, "swp_avg": 0})
    r = rows[0]
    cpu_used = round(float(r["avg_ut"] or 0), 2)
    return jsonify({
        "cpu_used": cpu_used,
        "cpu_free": round(100 - cpu_used, 2),
        "mem_avg":  round(float(r["avg_mem"] or 0), 2),
        "swp_avg":  round(float(r["avg_swp"] or 0), 2),
    })

# ── Daily APIs ───────────────────────────────────────────────────────────────

@app.route("/api/daily_node")
def api_daily_node():
    period     = request.args.get("period", "30d")
    ts_start, ts_end = parse_period(period)
    return jsonify(db.daily_node_summary(ts_start, ts_end))

@app.route("/api/daily_user")
def api_daily_user():
    period     = request.args.get("period", "30d")
    ts_start, ts_end = parse_period(period)
    return jsonify(db.daily_user_summary(ts_start, ts_end))

# ── Boot ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Starting LSF Monitor Dashboard ...")
    print(f"DB: {DB_PATH}")
    print(f"Listen: http://{LISTEN}:{PORT}")
    app.run(host=LISTEN, port=PORT, debug=False, threaded=True)
