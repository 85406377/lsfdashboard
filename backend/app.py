#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IBM LSF 作业监控 Dashboard 后端
"""

import os
import sys
import subprocess
import json
import socket
import platform
import random
import hashlib
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS

# 获取绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'dist'))
ASSETS_DIR = os.path.join(FRONTEND_DIST, 'assets')

app = Flask(__name__)
app.secret_key = 'lsf-dashboard-secret-key-2024'
CORS(app, supports_credentials=True)

# 用户数据文件
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
LOGO_FILE = os.path.join(BASE_DIR, 'logo.png')
DB_FILE = os.path.join(BASE_DIR, 'lsf_data.db')
ADMIN_USERNAME = 'admin'

print("FRONTEND_DIST:", FRONTEND_DIST)
print("ASSETS_DIR:", ASSETS_DIR)
print("DB_FILE:", DB_FILE)

# ==========================================
# 数据库初始化
# ==========================================

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 创建lsload表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lsload (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL,
            r1m REAL,
            r15m REAL,
            r60m REAL,
            utotal REAL,
            pg INTEGER,
            ls INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建历史作业表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bhist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            user TEXT,
            queue TEXT,
            status TEXT,
            submit_time DATETIME,
            start_time DATETIME,
            end_time DATETIME,
            exec_host TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 用户管理函数
# ==========================================

def load_users():
    """加载用户数据"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {ADMIN_USERNAME: {'password': hashlib.sha256('admin123').hexdigest(), 'role': 'admin'}}

def save_users(users):
    """保存用户数据"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def is_admin():
    """检查是否为admin用户"""
    return session.get('role') == 'admin'

def verify_linux_user(username, password):
    """验证Linux系统用户"""
    try:
        # 使用subprocess调用系统验证
        # 方法1: 使用python-pam (如果可用)
        # 方法2: 使用shadow文件验证 (需要root权限)
        # 方法3: 使用su命令验证
        
        # 使用su命令验证用户密码
        process = subprocess.Popen(
            ['su', '-', username, '-c', 'echo OK'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(input=(password + '\n').encode())
        
        if process.returncode == 0 and b'OK' in stdout:
            return True
        
        # 备用方法：使用pam认证
        try:
            import pam
            p = pam.pam()
            return p.authenticate(username, password)
        except ImportError:
            pass
        
        # 备用方法：使用ssh本地验证
        process = subprocess.Popen(
            ['sshpass', '-p', password, 'ssh', '-o', 'StrictHostKeyChecking=no', 
             '-o', 'NumberOfPasswordPrompts=1', 
             f'{username}@localhost', 'echo OK'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        return process.returncode == 0 and b'OK' in stdout
        
    except Exception as e:
        print(f"Linux user verification error: {e}")
        return False

# ==========================================
# LSF 命令执行
# ==========================================

def run_lsf_command(cmd, use_session_user=False):
    """执行 LSF 命令并返回结果
    
    Args:
        cmd: LSF命令
        use_session_user: 是否使用当前session用户的用户名作为-u参数
    """
    # 获取当前登录用户
    current_user = session.get('user', '')
    is_admin_user = is_admin()
    
    # admin用户使用 -u all
    if is_admin_user:
        if '-u ' in cmd:
            import re
            cmd = re.sub(r'-u\s+\S+', '-u all', cmd)
            print("Admin mode, modified command:", cmd)
        elif use_session_user:
            # admin用户查看所有
            cmd = cmd + ' -u all'
    else:
        # 非admin用户使用当前session用户名
        if use_session_user and current_user:
            if '-u ' in cmd:
                import re
                cmd = re.sub(r'-u\s+\S+', f'-u {current_user}', cmd)
            else:
                cmd = cmd + f' -u {current_user}'
            print(f"User {current_user} mode, modified command:", cmd)
    
    try:
        process = subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            return {'success': False, 'error': stderr.decode('utf-8', errors='ignore')}
        return {'success': True, 'output': stdout.decode('utf-8', errors='ignore')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_bjobs(output):
    jobs = []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return jobs
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 7:
            jobs.append({
                'job_id': parts[0], 'user': parts[1], 'status': parts[2],
                'queue': parts[3], 'host': parts[4] if len(parts) > 4 else 'N/A',
                'job_name': parts[5] if len(parts) > 5 else 'N/A',
                'slots': parts[6] if len(parts) > 6 else '1'
            })
    return jobs

def parse_bhosts(output):
    hosts = []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return hosts
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            hosts.append({
                'host_name': parts[0], 'status': parts[1],
                'r1m': parts[2] if len(parts) > 2 else 'N/A',
                'r15m': parts[3] if len(parts) > 3 else 'N/A'
            })
    return hosts

def parse_busers(output):
    users = []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return users
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            users.append({
                'user': parts[0], 'max': parts[1] if len(parts) > 1 else 'N/A',
                'njobs': parts[2] if len(parts) > 2 else '0',
                'run': parts[3] if len(parts) > 3 else '0'
            })
    return users

def parse_bqueues(output):
    queues = []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return queues
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 5:
            queues.append({
                'queue_name': parts[0], 'status': parts[1],
                'max': parts[2] if len(parts) > 2 else 'N/A',
                'njobs': parts[3] if len(parts) > 3 else '0',
                'run': parts[4] if len(parts) > 4 else '0'
            })
    return queues

def parse_lsload(output):
    loads = []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return loads
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 8:
            # 处理科学计数法 (如 2e+08)
            def safe_float(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 0
            
            def safe_int(val):
                try:
                    # 处理科学计数法
                    if 'e' in str(val).lower():
                        return int(float(val))
                    return int(val)
                except (ValueError, TypeError):
                    return 0
            
            loads.append({
                'host': parts[0],
                'r1m': safe_float(parts[2]) if len(parts) > 2 else 0,
                'r15m': safe_float(parts[4]) if len(parts) > 4 else 0,
                'r60m': safe_float(parts[6]) if len(parts) > 6 else 0,
                'utotal': safe_float(parts[7]) if len(parts) > 7 else 0,
                'pg': safe_int(parts[8]) if len(parts) > 8 else 0,
                'ls': safe_int(parts[9]) if len(parts) > 9 else 0
            })
    return loads

def parse_bhist(output):
    """解析bhist命令输出"""
    jobs = []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return jobs
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 8:
            job = {
                'job_id': parts[0],
                'user': parts[1] if len(parts) > 1 else 'N/A',
                'queue': parts[2] if len(parts) > 2 else 'N/A',
                'status': parts[3] if len(parts) > 3 else 'N/A',
                'submit_time': parts[4] + ' ' + parts[5] if len(parts) > 5 else 'N/A',
                'start_time': parts[6] + ' ' + parts[7] if len(parts) > 7 else 'N/A',
                'end_time': parts[8] + ' ' + parts[9] if len(parts) > 9 else 'N/A'
            }
            jobs.append(job)
    return jobs

# ==========================================
# 数据库操作
# ==========================================

def save_lsload_to_db(loads):
    """保存lsload数据到数据库"""
    if not loads:
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for load in loads:
        cursor.execute('''
            INSERT INTO lsload (host, r1m, r15m, r60m, utotal, pg, ls)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (load['host'], load['r1m'], load['r15m'], load.get('r60m', 0),
              load.get('utotal', 0), load.get('pg', 0), load.get('ls', 0)))
    conn.commit()
    conn.close()

def get_lsload_from_db(hosts=None, limit=60):
    """从数据库获取lsload数据"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if hosts:
        placeholders = ','.join(['?'] * len(hosts))
        cursor.execute(f'''
            SELECT * FROM lsload 
            WHERE host IN ({placeholders})
            ORDER BY timestamp DESC LIMIT ?
        ''', hosts + [limit])
    else:
        cursor.execute('SELECT * FROM lsload ORDER BY timestamp DESC LIMIT ?', [limit])
    
    rows = cursor.fetchall()
    conn.close()
    
    result = {}
    for row in rows:
        host = row['host']
        if host not in result:
            result[host] = []
        result[host].append({
            'r1m': row['r1m'],
            'r15m': row['r15m'],
            'r60m': row['r60m'],
            'utotal': row['utotal'],
            'pg': row['pg'],
            'ls': row['ls'],
            'timestamp': row['timestamp']
        })
    return result

# ==========================================
# 后台定时任务
# ==========================================

def background_task():
    """后台定时获取lsload数据"""
    while True:
        try:
            # 使用默认用户名运行lsload命令
            cmd = 'lsload -w'
            process = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='ignore')
                loads = parse_lsload(output)
                save_lsload_to_db(loads)
                print(f"lsload data saved: {len(loads)} records")
            else:
                print(f"lsload command failed: {stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"Error saving lsload: {e}")
        time.sleep(60)  # 每分钟执行一次

# 启动后台线程
bg_thread = threading.Thread(target=background_task, daemon=True)
bg_thread.start()

# ==========================================
# API 路由
# ==========================================

@app.route('/api/login', methods=['POST'])
def api_login():
    """用户登录"""
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type必须是application/json'}), 415
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': '用户名和密码不能为空'})
    
    users = load_users()
    
    # 检查是否为admin用户
    if username == ADMIN_USERNAME:
        if username in users and users[username]['password'] == hash_password(password):
            session['user'] = username
            session['role'] = 'admin'
            return jsonify({'success': True, 'user': username, 'role': 'admin'})
        return jsonify({'success': False, 'error': '用户名或密码错误'})
    
    # 非admin用户：使用Linux系统认证
    if verify_linux_user(username, password):
        session['user'] = username
        session['role'] = 'user'
        return jsonify({'success': True, 'user': username, 'role': 'user'})
    
    return jsonify({'success': False, 'error': 'Linux系统认证失败'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """用户登出"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/check-login', methods=['GET'])
def api_check_login():
    """检查登录状态"""
    if 'user' in session:
        return jsonify({'success': True, 'user': session['user'], 'role': session.get('role', 'user')})
    return jsonify({'success': False, 'error': '未登录'})

@app.route('/api/change-password', methods=['POST'])
def api_change_password():
    """修改密码"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': '未登录'})
    
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type必须是application/json'}), 415
    
    data = request.get_json()
    old_password = data.get('oldPassword', '')
    new_password = data.get('newPassword', '')
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'error': '密码不能为空'})
    
    users = load_users()
    username = session['user']
    
    if users[username]['password'] != hash_password(old_password):
        return jsonify({'success': False, 'error': '原密码错误'})
    
    users[username]['password'] = hash_password(new_password)
    save_users(users)
    
    return jsonify({'success': True, 'message': '密码修改成功'})

@app.route('/api/upload-logo', methods=['POST'])
def api_upload_logo():
    """上传企业Logo"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': '未登录'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有上传文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    
    if ext not in allowed_extensions:
        return jsonify({'success': False, 'error': '不支持的文件类型'})
    
    file.save(LOGO_FILE)
    return jsonify({'success': True, 'message': 'Logo上传成功'})

@app.route('/api/get-logo', methods=['GET'])
def api_get_logo():
    """获取Logo"""
    if os.path.exists(LOGO_FILE):
        return jsonify({'success': True, 'hasLogo': True})
    return jsonify({'success': True, 'hasLogo': False})

@app.route('/logo.png')
def serve_logo():
    """提供Logo文件"""
    if os.path.exists(LOGO_FILE):
        return send_from_directory(BASE_DIR, 'logo.png')
    return '', 404

@app.route('/api/system-info')
def api_system_info():
    """获取系统信息"""
    try:
        username = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
        hostname = socket.gethostname()
        os_version = platform.platform()
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            network_status = "Connected"
        except:
            network_status = "Disconnected"
        return jsonify({
            'username': username,
            'hostname': hostname,
            'os_version': os_version,
            'network_status': network_status,
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/jobs')
def api_jobs():
    """获取作业列表 - 使用当前登录用户"""
    result = run_lsf_command('bjobs -w', use_session_user=True)
    if result['success']:
        return jsonify({'success': True, 'data': parse_bjobs(result['output'])})
    return jsonify(result)

@app.route('/api/jobs/run')
def api_run_jobs():
    """获取Run状态作业列表，支持分页 - 使用当前登录用户"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 50, type=int)
    
    result = run_lsf_command('bjobs -w', use_session_user=True)
    if result['success']:
        all_jobs = parse_bjobs(result['output'])
        # 筛选RUN状态的作业
        run_jobs = [j for j in all_jobs if j['status'] == 'RUN']
        total = len(run_jobs)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = run_jobs[start:end]
        return jsonify({
            'success': True, 
            'data': page_data,
            'total': total,
            'page': page,
            'pageSize': page_size
        })
    return jsonify(result)

@app.route('/api/jobs/all')
def api_all_jobs():
    """获取所有作业列表，支持分页 - 使用当前登录用户"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 50, type=int)
    
    result = run_lsf_command('bjobs -w', use_session_user=True)
    if result['success']:
        all_jobs = parse_bjobs(result['output'])
        total = len(all_jobs)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = all_jobs[start:end]
        return jsonify({
            'success': True, 
            'data': page_data,
            'total': total,
            'page': page,
            'pageSize': page_size
        })
    return jsonify(result)

@app.route('/api/history')
def api_history():
    """获取历史作业，支持分页 - 使用当前登录用户"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 50, type=int)
    
    # 使用run_lsf_command自动处理-u参数
    result = run_lsf_command('bhist -w', use_session_user=True)
    if result['success']:
        all_jobs = parse_bhist(result['output'])
        total = len(all_jobs)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = all_jobs[start:end]
        return jsonify({
            'success': True, 
            'data': page_data,
            'total': total,
            'page': page,
            'pageSize': page_size
        })
    return jsonify(result)

@app.route('/api/hosts')
def api_hosts():
    result = run_lsf_command('bhosts -w')
    if result['success']:
        return jsonify({'success': True, 'data': parse_bhosts(result['output'])})
    return jsonify(result)

@app.route('/api/users')
def api_users():
    result = run_lsf_command('busers -w')
    if result['success']:
        return jsonify({'success': True, 'data': parse_busers(result['output'])})
    return jsonify(result)

@app.route('/api/queues')
def api_queues():
    result = run_lsf_command('bqueues -w')
    if result['success']:
        return jsonify({'success': True, 'data': parse_bqueues(result['output'])})
    return jsonify(result)

@app.route('/api/load')
def api_load():
    result = run_lsf_command('lsload -w')
    if result['success']:
        return jsonify({'success': True, 'data': parse_lsload(result['output'])})
    return jsonify(result)

@app.route('/api/load-db')
def api_load_from_db():
    """从数据库获取lsload数据"""
    limit = request.args.get('limit', 60, type=int)
    result = run_lsf_command('lsload -w')
    current_loads = []
    if result['success']:
        current_loads = parse_lsload(result['output'])
        # 保存到数据库
        save_lsload_to_db(current_loads)
    
    # 获取数据库中的历史数据
    hosts = [load['host'] for load in current_loads] if current_loads else None
    db_data = get_lsload_from_db(hosts, limit)
    
    return jsonify({'success': True, 'current': current_loads, 'history': db_data})

@app.route('/api/job/<job_id>')
def api_job_detail(job_id):
    result = run_lsf_command('bjobs -l %s' % job_id)
    if result['success']:
        return jsonify({'success': True, 'data': result['output']})
    return jsonify(result)

@app.route('/api/kill/<job_id>', methods=['POST'])
def api_kill_job(job_id):
    result = run_lsf_command('bkill %s' % job_id)
    return jsonify(result)

@app.route('/api/load-trend')
def api_load_trend():
    result = run_lsf_command('lsload -w')
    current_loads = []
    if result['success']:
        current_loads = parse_lsload(result['output'])
    trend_data = []
    hosts = set([load['host'] for load in current_loads]) if current_loads else ['localhost']
    for i in range(12):
        time_point = (datetime.now() - timedelta(minutes=(11-i)*5)).strftime('%H:%M')
        for host in hosts:
            base_load = 2.0 + random.random() * 3.0
            trend_data.append({
                'time': time_point, 'host': host,
                'r1m': round(base_load + random.random(), 2),
                'r15m': round(base_load + random.random() * 0.5, 2)
            })
    return jsonify({'success': True, 'data': trend_data})

# ==========================================
# 前端静态文件路由
# ==========================================

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIST, 'index.html')

@app.route('/<path:path>')
def serve_spa(path):
    if path.startswith('api/') or path.startswith('assets/') or path == 'logo.png':
        return jsonify({'error': 'Not Found'}), 404
    return send_from_directory(FRONTEND_DIST, 'index.html')

if __name__ == '__main__':
    print("Starting LSF Dashboard Server...")
    print("Access at: http://localhost:5002")
    app.run(host='0.0.0.0', port=5002, debug=False)
