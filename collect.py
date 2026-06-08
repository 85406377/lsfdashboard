#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect.py — LSF Monitor 数据采集主程序
每分钟采集 lsload 和 busers all 的输出，写入 SQLite 数据库。
支持 systemd service 或独立前台/后台运行。
"""

import logging
import logging.handlers
import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from db import Database

# ──────────────────────────────────────────────
#  日志配置
# ──────────────────────────────────────────────

def setup_logging(log_path):
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024,
        backupCount=5, encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logging.getLogger().addHandler(file_handler)


# ──────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────

def _strip_unit(s, to_gb=False):
    """Strip G/M/K suffix and return float. If to_gb=True, convert M/K → GB."""
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    for sufx, factor in (("G", 1), ("g", 1), ("M", 1/1024), ("m", 1/1024), ("K", 1/1024/1024), ("k", 1/1024/1024)):
        if s.endswith(sufx) and len(s) > 1:
            try:
                val = float(s[:-1])
                return val * factor if to_gb else val
            except ValueError:
                pass
    return float(s) if s else 0.0


def _safe_float(s, default=0.0):
    try:
        return float(str(s).replace("%", "").replace("-", ""))
    except (ValueError, TypeError):
        return default


def _safe_int(s, default=0):
    try:
        return int(str(s).replace("%", "").replace("-", ""))
    except (ValueError, TypeError):
        return default


# ──────────────────────────────────────────────
#  lsload 解析
# ──────────────────────────────────────────────

def parse_lsload(output, ts):
    """
    lsload 真实格式（空格分隔，字段位置固定）：
      HOST_NAME  status  r15s  r1m  r15m  ut  pg  ls  it  tmp  swp  mem
      node1      ok      0.7   0.6  0.7   2%  0.0  5   5752 68G  141M 76.3G

    字段映射：
      [0] hostname   节点名
      [1] status     ok / unavail
      [2] r15s       15秒负载
      [3] r1m        1分钟负载
      [4] r15m       15分钟负载
      [5] ut         CPU利用率 2%
      [6] pg         页换入率
      [7] ls         登录shell数
      [8] it         中断数
      [9] tmp        临时空间（68G）
      [10] swp       交换区（141M）
      [11] mem       物理内存总量（76.3G）

    跳过 status != 'ok' 的行（节点离线）。
    """
    lines = output.strip().splitlines()
    rows = []

    for line in lines:
        parts = line.split()
        if len(parts) < 12:
            # 跳过表头行和字段不足的行
            continue
        # parts[1] = 'ok' 表示节点正常，'unavail' 表示离线
        if parts[1] != "ok":
            logging.warning("lsload 节点离线: %s", parts[0])
            continue
        try:
            ut_raw = parts[5].replace("%", "").replace("-", "")
            rows.append({
                "hostname": parts[0],
                "status":   parts[1],
                "r15s":     _safe_float(parts[2]),
                "r1m":      _safe_float(parts[3]),
                "r15m":     _safe_float(parts[4]),
                "ut":       _safe_float(ut_raw),
                "pg":       _safe_float(parts[6]),
                "ls":       _safe_int(parts[7]),
                "it":       _safe_float(parts[8]),
                "tmp":      _strip_unit(parts[9]),
                "swp":      _strip_unit(parts[10], to_gb=True),
                "mem":      _strip_unit(parts[11]),
                "ts":       ts.strftime("%Y-%m-%d %H:%M:%S"),
            })
        except (ValueError, IndexError) as e:
            logging.warning("解析 lsload 行失败 [%s]: %s", str(e), line[:80])
            continue

    return rows


# ──────────────────────────────────────────────
#  busers 解析
# ──────────────────────────────────────────────

def parse_busers(output, ts):
    """
    busers all 真实格式（空格分隔）：
      USER/GROUP  JL/P  MAX  NJOBS  PEND  RUN  SSUSP  USUSP  RSV
      annie       -     128  16     0     16   0     0      0

    字段映射：
      [0] username
      [1] JL/P（不用）
      [2] MAX（不用）
      [3] NJOBS（不用）
      [4] PEND
      [5] RUN
      [6] SSUSP
      [7] USUSP
      [8] RSV

    跳过首行（表头）和全 '-' 行。
    """
    lines = output.strip().splitlines()
    rows = []

    for line in lines:
        parts = line.split()
        if len(parts) < 6:
            continue
        # 跳过表头行
        if parts[0] in ("USER/GROUP", "USER_NAME", "GROUP_NAME"):
            continue
        # 跳过全 '-' 行（如 default 行）
        if all(str(p).strip() == "-" for p in parts):
            continue
        try:
            rows.append({
                "username": parts[0],
                "pend":     _safe_int(parts[4]) if len(parts) > 4 and parts[4] != "-" else 0,
                "run":      _safe_int(parts[5]) if parts[5] != "-" else 0,
                "ssusp":    _safe_int(parts[6]) if len(parts) > 6 and parts[6] != "-" else 0,
                "ususp":    _safe_int(parts[7]) if len(parts) > 7 and parts[7] != "-" else 0,
                "rsv":      _safe_int(parts[8]) if len(parts) > 8 and parts[8] != "-" else 0,
                "ts":       ts.strftime("%Y-%m-%d %H:%M:%S"),
            })
        except (ValueError, IndexError) as e:
            logging.warning("解析 busers 行失败 [%s]: %s", str(e), line[:80])
            continue

    return rows


# ──────────────────────────────────────────────
#  命令执行
# ──────────────────────────────────────────────

def run_lsf_command(cmd, timeout=10):
    """
    本地执行 LSF 命令，不走 SSH。
    Python 2.7 / 3.6 兼容写法。
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, err)
    return out.decode("utf-8", errors="replace")


# ──────────────────────────────────────────────
#  采集循环
# ──────────────────────────────────────────────

def collect_once(db, config, ts):
    log = logging.getLogger("collect")
    timeout  = config.get("lsf_cmd_timeout", 10)
    cmds_cfg = config.get("commands", {})
    ok = True

    # ── lsload ──
    try:
        raw = run_lsf_command(cmds_cfg.get("lsload", ["lsload"]), timeout=timeout)
        rows = parse_lsload(raw, ts)
        if rows:
            db.insert_lsload(rows)
            log.info("lsload → %d 条记录写入 [%s]", len(rows), ts)
        else:
            log.warning("lsload 解析结果为空 [%s]", ts)
    except subprocess.TimeoutExpired:
        log.error("lsload 命令执行超时（%ds）", timeout)
        ok = False
    except subprocess.CalledProcessError as e:
        log.error("lsload 命令失败，返回码 %d: %s", e.returncode, e.stderr)
        ok = False
    except Exception as e:
        log.error("lsload 采集异常: %s", str(e))
        ok = False

    # ── busers all ──
    try:
        raw = run_lsf_command(cmds_cfg.get("busers", ["busers", "all"]), timeout=timeout)
        rows = parse_busers(raw, ts)
        if rows:
            db.insert_busers(rows)
            log.info("busers all → %d 条记录写入 [%s]", len(rows), ts)
        else:
            log.warning("busers all 解析结果为空 [%s]", ts)
    except subprocess.TimeoutExpired:
        log.error("busers all 命令执行超时（%ds）", timeout)
        ok = False
    except subprocess.CalledProcessError as e:
        log.error("busers all 命令失败，返回码 %d: %s", e.returncode, e.stderr)
        ok = False
    except Exception as e:
        log.error("busers all 采集异常: %s", str(e))
        ok = False

    return ok


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LSF Monitor 数据采集器")
    parser.add_argument("--config", default=str(BASE_DIR / "config.json"),
                        help="配置文件路径（默认同目录 config.json）")
    parser.add_argument("--once", action="store_true",
                        help="仅采集一次（不循环，用于调试）")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)

    log_path = config.get("log_path", "/var/log/lsf-monitor/collect.log")
    setup_logging(log_path)
    log = logging.getLogger("collect")

    log.info("=== LSF Monitor 采集器启动 ===  config=%s", args.config)

    db_path = config.get("db_path", "/var/lib/lsf-monitor/lsf_monitor.db")
    db = Database(db_path)
    try:
        db.init_schema()
    except Exception as e:
        log.error("数据库初始化失败: %s", str(e))
        sys.exit(1)

    interval = config.get("interval", 60)

    if args.once:
        ts = datetime.now()
        ok = collect_once(db, config, ts)
        sys.exit(0 if ok else 1)

    while True:
        ts = datetime.now()
        collect_once(db, config, ts)
        time.sleep(interval)


if __name__ == "__main__":
    main()
