#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py — LSF Monitor Tkinter GUI
在 CentOS 图形界面直接运行，或通过 ssh -X 转发到 Windows。
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta

try:
    import Tkinter as tk
    import ttk
except ImportError:
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        print("ERROR: Tkinter not available")
        sys.exit(1)

try:
    import tkinter.font as tkfont
except ImportError:
    try:
        import tkFont as tkfont
    except Exception:
        tkfont = None

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
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"db_path": str(BASE_DIR / "lsf_monitor.db"),
                "log_path": str(BASE_DIR / "collect.log"),
                "interval": 60}

config  = load_config()
DB_PATH = config.get("db_path", str(BASE_DIR / "lsf_monitor.db"))

# ──────────────────────────────────────────────
#  Process control
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
        os.kill(pid, 15)
    except OSError:
        pass
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    return "stopped"

# ──────────────────────────────────────────────
#  Font helper
# ──────────────────────────────────────────────

def FONT(size=11, weight="normal"):
    if tkfont:
        return tkfont.Font(family="Arial", size=size, weight=weight)
    return ("Arial", size)

# ──────────────────────────────────────────────
#  Main App
# ──────────────────────────────────────────────

class LSFMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LSF Monitor")
        self.geometry("950x640")
        self.minsize(800, 500)

        self._status_job = None

        self._build_ui()
        self._poll_status()
        self._auto_refresh()

        # load dropdowns after startup
        self.after(500, self._load_lists)

    # ── UI building ──────────────────────────────

    def _build_ui(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        # ── Title bar ──
        title = tk.Frame(frame, bg="#1a73e8", height=48)
        title.pack(fill=tk.X)
        title.pack_propagate(False)
        tk.Label(title, text="LSF Monitor",
                 font=FONT(17, "bold"),
                 fg="white", bg="#1a73e8").pack(side=tk.LEFT, padx=16, pady=6)
        self._status_lbl = tk.Label(title, text="checking...",
                                     font=FONT(11), fg="#dddddd", bg="#1a73e8")
        self._status_lbl.pack(side=tk.RIGHT, padx=16, pady=6)

        # ── Control strip ──
        ctrl = tk.Frame(frame, bg="#f0f2f5", pady=8, padx=16)
        ctrl.pack(fill=tk.X)

        tk.Label(ctrl, text="Collector:", font=FONT(11), bg="#f0f2f5").pack(side=tk.LEFT)

        self._btn_start = tk.Button(ctrl, text="Start",
                                     font=FONT(10, "bold"),
                                     bg="#34a853", fg="white",
                                     activebackground="#2d9147",
                                     relief=tk.FLAT, padx=20, pady=3,
                                     command=self._on_start)
        self._btn_start.pack(side=tk.LEFT, padx=5)

        self._btn_stop = tk.Button(ctrl, text="Stop",
                                    font=FONT(10, "bold"),
                                    bg="#ea4335", fg="white",
                                    activebackground="#c5221f",
                                    relief=tk.FLAT, padx=20, pady=3,
                                    command=self._on_stop)
        self._btn_stop.pack(side=tk.LEFT, padx=5)

        self._pid_lbl = tk.Label(ctrl, text="", font=FONT(10),
                                  fg="#666666", bg="#f0f2f5")
        self._pid_lbl.pack(side=tk.LEFT, padx=16)

        # ── Notebook ──
        nb = ttk.Notebook(frame)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 10))

        nb.add(self._build_overview_tab(), text="Overview")
        nb.add(self._build_host_ut_tab(), text="Host UT Trend")
        nb.add(self._build_user_run_tab(), text="User RUN Trend")

    # ── Tab: Overview ───────────────────────────

    def _build_overview_tab(self):
        f = tk.Frame(padx=12, pady=10)

        # Nodes
        tk.Label(f, text="Nodes", font=FONT(12, "bold"), anchor="w").\
            pack(fill=tk.X, pady=(0, 5))

        hx = tk.Scrollbar(f, orient=tk.HORIZONTAL)
        hy = tk.Scrollbar(f, orient=tk.VERTICAL)
        hcols  = ["hostname","status","r15s","r1m","r15m","ut","pg","ls","it","tmp","swp","mem","ts"]
        hheads = ["Hostname","Status","r15s","r1m","r15m","UT(%)","PG","LS","IT","Tmp","Swp","Mem(GB)","Last Update"]
        self._host_tree = ttk.Treeview(f, columns=hcols, show="headings",
                                        xscrollcommand=hx.set, yscrollcommand=hy.set, height=7)
        hx.config(command=self._host_tree.xview)
        hy.config(command=self._host_tree.yview)
        hx.pack(side=tk.BOTTOM, fill=tk.X)
        hy.pack(side=tk.RIGHT, fill=tk.Y)
        for col, hdr in zip(hcols, hheads):
            self._host_tree.heading(col, text=hdr)
            self._host_tree.column(col, width=110, anchor="w")
        self._host_tree.pack(fill=tk.X, pady=(0, 10))

        # Users
        tk.Label(f, text="Users", font=FONT(12, "bold"), anchor="w").\
            pack(fill=tk.X, pady=(0, 5))

        uy = tk.Scrollbar(f, orient=tk.VERTICAL)
        ucols  = ["username","pend","run","ssusp","ususp","rsv","ts"]
        uheads = ["Username","PEND","RUN","SSUSP","USUSP","RSV","Last Update"]
        self._user_tree = ttk.Treeview(f, columns=ucols, show="headings",
                                        yscrollcommand=uy.set, height=6)
        uy.config(command=self._user_tree.yview)
        uy.pack(side=tk.RIGHT, fill=tk.Y)
        for col, hdr in zip(ucols, uheads):
            self._user_tree.heading(col, text=hdr)
            self._user_tree.column(col, width=130, anchor="w")
        self._user_tree.pack(fill=tk.X)

        tk.Button(f, text="Refresh Overview", command=self._load_overview,
                  bg="#1a73e8", fg="white", relief=tk.FLAT, padx=14, pady=3,
                  font=FONT(10)).pack(pady=(10, 0))

        return f

    # ── Tab: Host UT ─────────────────────────────

    def _build_host_ut_tab(self):
        f = tk.Frame(padx=12, pady=10)

        bar = tk.Frame(f)
        bar.pack(fill=tk.X, pady=(0, 8))

        tk.Label(bar, text="Host:", font=FONT(11)).pack(side=tk.LEFT)
        self._host_var = tk.StringVar()
        self._host_cbox = ttk.Combobox(bar, textvariable=self._host_var,
                                       width=22, state="readonly", font=FONT(11))
        self._host_cbox.pack(side=tk.LEFT, padx=(4, 12))

        tk.Label(bar, text="Period:", font=FONT(11)).pack(side=tk.LEFT)
        self._hper_var = tk.StringVar(value="day")
        ttk.Combobox(bar, textvariable=self._hper_var, width=8,
                     values=["hour","day","month"], state="readonly", font=FONT(11))\
            .pack(side=tk.LEFT, padx=(4, 12))

        tk.Label(bar, text="Limit:", font=FONT(11)).pack(side=tk.LEFT)
        self._hlmt_var = tk.StringVar(value="30")
        tk.Entry(bar, textvariable=self._hlmt_var, width=6, font=FONT(11))\
            .pack(side=tk.LEFT, padx=(4, 12))

        tk.Button(bar, text="Query", command=self._load_host_ut,
                  bg="#1a73e8", fg="white", relief=tk.FLAT, padx=16, pady=2,
                  font=FONT(11)).pack(side=tk.LEFT, padx=(4, 0))

        hx2 = tk.Scrollbar(f, orient=tk.HORIZONTAL)
        hy2 = tk.Scrollbar(f, orient=tk.VERTICAL)
        hcols2  = ["bucket","avg_ut","sample_count"]
        hheads2 = ["Bucket","Avg UT(%)","Samples"]
        self._hut_tree = ttk.Treeview(f, columns=hcols2, show="headings",
                                       xscrollcommand=hx2.set, yscrollcommand=hy2.set)
        hx2.config(command=self._hut_tree.xview)
        hy2.config(command=self._hut_tree.yview)
        hx2.pack(side=tk.BOTTOM, fill=tk.X)
        hy2.pack(side=tk.RIGHT, fill=tk.Y)
        for col, hdr in zip(hcols2, hheads2):
            self._hut_tree.heading(col, text=hdr)
            self._hut_tree.column(col, width=145, anchor="w")
        self._hut_tree.pack(fill=tk.BOTH, expand=True)

        return f

    # ── Tab: User RUN ────────────────────────────

    def _build_user_run_tab(self):
        f = tk.Frame(padx=12, pady=10)

        bar = tk.Frame(f)
        bar.pack(fill=tk.X, pady=(0, 8))

        tk.Label(bar, text="User:", font=FONT(11)).pack(side=tk.LEFT)
        self._user_var = tk.StringVar()
        self._user_cbox = ttk.Combobox(bar, textvariable=self._user_var,
                                        width=22, state="readonly", font=FONT(11))
        self._user_cbox.pack(side=tk.LEFT, padx=(4, 12))

        tk.Label(bar, text="Period:", font=FONT(11)).pack(side=tk.LEFT)
        self._uper_var = tk.StringVar(value="day")
        ttk.Combobox(bar, textvariable=self._uper_var, width=8,
                     values=["hour","day","month"], state="readonly", font=FONT(11))\
            .pack(side=tk.LEFT, padx=(4, 12))

        tk.Label(bar, text="Limit:", font=FONT(11)).pack(side=tk.LEFT)
        self._ulmt_var = tk.StringVar(value="30")
        tk.Entry(bar, textvariable=self._ulmt_var, width=6, font=FONT(11))\
            .pack(side=tk.LEFT, padx=(4, 12))

        tk.Button(bar, text="Query", command=self._load_user_run,
                  bg="#1a73e8", fg="white", relief=tk.FLAT, padx=16, pady=2,
                  font=FONT(11)).pack(side=tk.LEFT, padx=(4, 0))

        uy2 = tk.Scrollbar(f, orient=tk.VERTICAL)
        ucols2  = ["bucket","avg_run","max_run","min_run","sample_count"]
        uheads2 = ["Bucket","Avg RUN","Max RUN","Min RUN","Samples"]
        self._urun_tree = ttk.Treeview(f, columns=ucols2, show="headings",
                                       yscrollcommand=uy2.set)
        uy2.config(command=self._urun_tree.yview)
        uy2.pack(side=tk.RIGHT, fill=tk.Y)
        for col, hdr in zip(ucols2, uheads2):
            self._urun_tree.heading(col, text=hdr)
            self._urun_tree.column(col, width=165, anchor="w")
        self._urun_tree.pack(fill=tk.BOTH, expand=True)

        return f

    # ── Status polling ───────────────────────────

    def _poll_status(self):
        running = is_running()
        pid     = get_pid()
        if running:
            self._status_lbl.config(text="  Running  (PID %s)  " % (pid or "?"), fg="#a8f0a0")
            self._btn_start.config(state=tk.DISABLED)
            self._btn_stop.config(state=tk.NORMAL)
            self._pid_lbl.config(text="PID: %s" % (pid or ""))
        else:
            self._status_lbl.config(text="  Stopped  ", fg="#ff8888")
            self._btn_start.config(state=tk.NORMAL)
            self._btn_stop.config(state=tk.DISABLED)
            self._pid_lbl.config(text="")
        self._status_job = self.after(3000, self._poll_status)

    def _auto_refresh(self):
        self._load_overview()
        self.after(60000, self._auto_refresh)

    # ── Actions ─────────────────────────────────

    def _on_start(self):
        msg = start_collect()
        self._popup(msg)

    def _on_stop(self):
        msg = stop_collect()
        self._popup(msg)

    def _popup(self, msg):
        w = tk.Toplevel(self)
        w.title("Info")
        w.geometry("300x80")
        w.resizable(False, False)
        w.grab_set()
        tk.Label(w, text=msg, font=FONT(12), wraplength=270, pady=14).pack(fill=tk.BOTH)
        tk.Button(w, text="OK", command=w.destroy, width=10, font=FONT(10)).pack(pady=(0, 10))

    # ── Data loading ─────────────────────────────

    def _load_overview(self):
        if Database is None:
            return
        try:
            db = Database(DB_PATH)
            self._fill(self._host_tree,
                       db.query_overview(),
                       ["hostname","status","r15s","r1m","r15m","ut","pg","ls","it","tmp","swp","mem","ts"])
            self._fill(self._user_tree,
                       db.query_user_overview(),
                       ["username","pend","run","ssusp","ususp","rsv","ts"])
        except Exception:
            pass

    def _load_host_ut(self):
        self._load_dropdown(self._host_cbox, self._host_var,
                            "SELECT DISTINCT hostname FROM lsload_snapshot ORDER BY hostname")
        hostname = self._host_var.get().strip()
        period   = self._hper_var.get()
        try:
            limit = int(self._hlmt_var.get())
        except ValueError:
            limit = 30
        if not hostname or Database is None:
            return
        ts_end = datetime.now()
        if period == "hour":
            ts_start = ts_end - timedelta(hours=limit)
        elif period == "day":
            ts_start = ts_end - timedelta(days=limit)
        else:
            ts_start = ts_end - timedelta(days=limit * 30)
        try:
            db = Database(DB_PATH)
            rows = db.query_host_ut(hostname, period, limit, ts_start=ts_start, ts_end=ts_end)
            self._fill(self._hut_tree, rows,
                        ["bucket","avg_ut","sample_count"])
        except Exception:
            pass

    def _load_user_run(self):
        self._load_dropdown(self._user_cbox, self._user_var,
                            "SELECT DISTINCT username FROM busers_snapshot ORDER BY username")
        username = self._user_var.get().strip()
        period   = self._uper_var.get()
        try:
            limit = int(self._ulmt_var.get())
        except ValueError:
            limit = 30
        if not username or Database is None:
            return
        ts_end = datetime.now()
        if period == "hour":
            ts_start = ts_end - timedelta(hours=limit)
        elif period == "day":
            ts_start = ts_end - timedelta(days=limit)
        else:
            ts_start = ts_end - timedelta(days=limit * 30)
        try:
            db = Database(DB_PATH)
            rows = db.query_user_run(username, period, limit, ts_start=ts_start, ts_end=ts_end)
            self._fill(self._urun_tree, rows,
                        ["bucket","avg_run","max_run","min_run","sample_count"])
        except Exception:
            pass

    def _fill(self, tree, rows, cols):
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tree.insert("", "end", values=[row.get(c, "") for c in cols])

    # ── Dropdown lists ───────────────────────────

    def _load_dropdown(self, cbox, var, sql):
        """Refresh a single combobox from SQL, preserving current selection."""
        if Database is None:
            return
        try:
            db = Database(DB_PATH)
            conn = db._conn()
            try:
                cur = conn.execute(sql)
                items = [r[0] for r in cur.fetchall()]
                current = var.get()
                cbox["values"] = items
                if current in items:
                    var.set(current)
                elif items:
                    var.set(items[0])
            finally:
                db._close_conn(conn)
        except Exception:
            pass

    def _load_lists(self):
        if Database is None:
            return
        try:
            db = Database(DB_PATH)
            conn = db._conn()
            try:
                cur = conn.execute(
                    "SELECT DISTINCT hostname FROM lsload_snapshot ORDER BY hostname")
                self._host_cbox["values"] = [r[0] for r in cur.fetchall()]
            finally:
                db._close_conn(conn)
        except Exception:
            pass
        try:
            db = Database(DB_PATH)
            conn = db._conn()
            try:
                cur = conn.execute(
                    "SELECT DISTINCT username FROM busers_snapshot ORDER BY username")
                self._user_cbox["values"] = [r[0] for r in cur.fetchall()]
            finally:
                db._close_conn(conn)
        except Exception:
            pass
        self._load_overview()


# ──────────────────────────────────────────────
#  Boot
# ──────────────────────────────────────────────

if __name__ == "__main__":
    LSFMonitorApp().mainloop()
