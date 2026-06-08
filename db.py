#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db.py — LSF Monitor 数据库操作
"""

import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Schema
# ──────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS lsload_snapshot (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname  TEXT    NOT NULL,
    status    TEXT,
    r15s      REAL,
    r1m       REAL,
    r15m      REAL,
    ut        REAL,
    pg        REAL,
    ls        INTEGER,
    it        REAL,
    tmp       REAL,
    swp       REAL,
    mem       REAL,
    ts        DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS busers_snapshot (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT    NOT NULL,
    pend      INTEGER,
    run       INTEGER,
    ssusp     INTEGER,
    ususp     INTEGER,
    rsv       INTEGER,
    ts        DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lsload_ts_hostname
    ON lsload_snapshot(ts, hostname);

CREATE INDEX IF NOT EXISTS idx_lsload_hostname_ts
    ON lsload_snapshot(hostname, ts);

CREATE INDEX IF NOT EXISTS idx_busers_ts_username
    ON busers_snapshot(ts, username);

CREATE INDEX IF NOT EXISTS idx_busers_username_ts
    ON busers_snapshot(username, ts);
"""


# ──────────────────────────────────────────────
#  Connection manager
# ──────────────────────────────────────────────

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._ensure_dir()

    def _ensure_dir(self):
        d = os.path.dirname(self.db_path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)

    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=60, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 60000")
        return conn

    def _close_conn(self, conn):
        try:
            conn.close()
        except Exception:
            pass

    def init_schema(self):
        conn = self._conn()
        try:
            conn.executescript(SCHEMA)
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                logger.warning("数据库被锁定，跳过建表（表/索引可能已存在）: %s", e)
            else:
                raise
        finally:
            self._close_conn(conn)
        logger.info("数据库初始化完成: %s", self.db_path)

    # ──────────────────────────────────────────
    #  Insert
    # ──────────────────────────────────────────

    def insert_lsload(self, rows):
        if not rows:
            return
        sql = """
        INSERT INTO lsload_snapshot
            (hostname, status, r15s, r1m, r15m, ut, pg, ls, it, tmp, swp, mem, ts)
        VALUES (:hostname, :status, :r15s, :r1m, :r15m, :ut, :pg, :ls, :it, :tmp, :swp, :mem, :ts)
        """
        conn = self._conn()
        try:
            conn.executemany(sql, rows)
            conn.commit()
        finally:
            self._close_conn(conn)
        logger.debug("写入 lsload 记录 %d 条", len(rows))

    def insert_busers(self, rows):
        if not rows:
            return
        sql = """
        INSERT INTO busers_snapshot
            (username, pend, run, ssusp, ususp, rsv, ts)
        VALUES (:username, :pend, :run, :ssusp, :ususp, :rsv, :ts)
        """
        conn = self._conn()
        try:
            conn.executemany(sql, rows)
            conn.commit()
        finally:
            self._close_conn(conn)
        logger.debug("写入 busers 记录 %d 条", len(rows))

    # ──────────────────────────────────────────
    #  Query helpers
    # ──────────────────────────────────────────

    @staticmethod
    def _strftime(ts):
        return ts.strftime("%Y-%m-%d %H:%M:%S")

    def _rows_to_dicts(self, rows):
        return [dict(r) for r in rows]

    def query_host_ut(self, hostname, period, limit=24, ts_end=None, ts_start=None):
        trunc_map = {
            "hour":  "strftime('%Y-%m-%d %H:00:00', ts)",
            "day":   "strftime('%Y-%m-%d', ts)",
            "month": "strftime('%Y-%m', ts)",
        }
        bucket_sql = trunc_map[period]

        sql = (
            "SELECT "
            + bucket_sql + " AS bucket, "
            + "AVG(ut) AS avg_ut, COUNT(*) AS sample_count "
            + "FROM lsload_snapshot "
            + "WHERE hostname = ? AND ts >= ? AND ts <= ? "
            + "GROUP BY bucket ORDER BY bucket ASC LIMIT ?"
        )

        if ts_end is None:
            ts_end = datetime.now()
        if ts_start is None:
            ts_start = ts_end

        conn = self._conn()
        try:
            cur = conn.execute(sql, (hostname, self._strftime(ts_start), self._strftime(ts_end), limit))
            return self._rows_to_dicts(cur.fetchall())
        finally:
            self._close_conn(conn)

    def query_user_run(self, username, period, limit=30, ts_end=None, ts_start=None):
        trunc_map = {
            "hour":  "strftime('%Y-%m-%d %H:00:00', ts)",
            "day":   "strftime('%Y-%m-%d', ts)",
            "month": "strftime('%Y-%m', ts)",
        }
        bucket_sql = trunc_map[period]

        sql = (
            "SELECT "
            + bucket_sql + " AS bucket, "
            + "AVG(run) AS avg_run, MAX(run) AS max_run, MIN(run) AS min_run, "
            + "COUNT(*) AS sample_count "
            + "FROM busers_snapshot "
            + "WHERE username = ? AND ts >= ? AND ts <= ? "
            + "GROUP BY bucket ORDER BY bucket ASC LIMIT ?"
        )

        if ts_end is None:
            ts_end = datetime.now()
        if ts_start is None:
            ts_start = ts_end

        conn = self._conn()
        try:
            cur = conn.execute(sql, (username, self._strftime(ts_start), self._strftime(ts_end), limit))
            return self._rows_to_dicts(cur.fetchall())
        finally:
            self._close_conn(conn)

    def query_overview(self):
        sql = """
        SELECT l.hostname, l.status, l.r15s, l.r1m, l.r15m,
               l.ut, l.pg, l.ls, l.it, l.tmp, l.swp, l.mem, l.ts
        FROM lsload_snapshot l
        INNER JOIN (
            SELECT hostname, MAX(ts) AS max_ts
            FROM lsload_snapshot GROUP BY hostname
        ) r ON l.hostname = r.hostname AND l.ts = r.max_ts
        ORDER BY l.hostname
        """
        conn = self._conn()
        try:
            cur = conn.execute(sql)
            return self._rows_to_dicts(cur.fetchall())
        finally:
            self._close_conn(conn)

    def query_user_overview(self):
        sql = """
        SELECT b.username, b.pend, b.run, b.ssusp, b.ususp, b.rsv, b.ts
        FROM busers_snapshot b
        INNER JOIN (
            SELECT username, MAX(ts) AS max_ts
            FROM busers_snapshot GROUP BY username
        ) r ON b.username = r.username AND b.ts = r.max_ts
        ORDER BY b.username
        """
        conn = self._conn()
        try:
            cur = conn.execute(sql)
            return self._rows_to_dicts(cur.fetchall())
        finally:
            self._close_conn(conn)