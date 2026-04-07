#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IBM LSF 作业监控 Dashboard 后端 - 带登录功能和管理员权限
兼容 Python 2.7.5
"""

import os
import sys
import subprocess
import json
import socket
import platform
import random
from datetime import datetime, timedelta
import sqlite3
from functools import wraps

try:
    import spwd
    import pwd
    import crypt
    SYSTEM_AUTH_AVAILABLE = True
except ImportError:
    SYSTEM_AUTH_AVAILABLE = False

from flask import Flask, jsonify, request, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# 获取绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'dist'))
ASSETS_DIR = os.path.join(FRONTEND_DIST, 'assets')
DB_PATH = os.path.join(BASE_DIR, 'lsf_history.db')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'lsf-dashboard-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# Flask-Login 配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

# ==========================================
# 配置文件管理
# ==========================================
def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # 默认配置
        default_config = {
            "admin_users": ["admin"],
            "company_logo": "",
            "company_name": "LSF Dashboard"
        }
        save_config(default_config)
        return default_config

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# 初始化配置
CONFIG = load_config()

# ==========================================
# 数据库初始化
# ==========================================
def init_db():
    """初始化 SQLite 数据库，创建 job_history 表和用户配置表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_history (
            bid INTEGER PRIMARY KEY,
            buser TEXT,
            command TEXT,
            status TEXT,
            start_time TEXT,
            end_time TEXT,
            host TEXT,
            slots INTEGER DEFAULT 0,
            count INTEGER DEFAULT 1,
            exit_code INTEGER DEFAULT 0,
            submitted_at TEXT,
            created_at TEXT
        )
    ''')
    # 创建用户配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            username TEXT PRIMARY KEY,
            display_name TEXT,
            email TEXT,
            theme TEXT DEFAULT 'light',
            language TEXT DEFAULT 'zh-CN',
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    # 创建索引以提高查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_buser ON job_history(buser)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON job_history(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_submitted_at ON job_history(submitted_at)')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# 启动时初始化数据库
init_db()

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

print("FRONTEND_DIST:", FRONTEND_DIST)
print("ASSETS_DIR:", ASSETS_DIR)
print("Assets exist:", os.path.exists(ASSETS_DIR))
if os.path.exists(ASSETS_DIR):
    print("Assets files:", os.listdir(ASSETS_DIR))

# ==========================================
# Flask-Login 用户管理
# ==========================================
class User(UserMixin):
    def __init__(self, username):
        self.id = username
    
    @staticmethod
    def get_user(username):
        user = User(username)
        return user

@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

# ==========================================
# 权限检查装饰器
# ==========================================
def require_auth(f):
    """自定义登录装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            # 判断是否是 API 请求
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Unauthorized', 'requires_auth': True}), 401
            else:
                # 重定向到登录页
                return redirect(url_for('login_page') + '?next=' + request.path)
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        username = session.get('username', '')
        if username not in CONFIG.get('admin_users', ['admin']):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# 系统级认证（使用 /etc/shadow）
# ==========================================
import crypt
import spwd
import pwd

def authenticate_user(username, password):
    """使用系统级认证验证本地用户凭证（读取 /etc/shadow）"""
    try:
        # 首先检查用户是否存在
        try:
            pwd.getpwnam(username)
        except KeyError:
            print(f"User {username} does not exist")
            return False
        
        # 获取 shadow 密码条目
        shadow_entry = spwd.getspnam(username)
        encrypted_password = shadow_entry.sp_pwdp
        
        # 如果密码字段为 * 或 !，表示账户被锁定或无密码
        if encrypted_password in ['*', '!', '!!', '']:
            print(f"User {username} has locked or no password")
            return False
        
        # 使用 crypt 验证密码
        # crypt.crypt 会自动从加密密码中提取 salt
        hashed = crypt.crypt(password, encrypted_password)
        
        if hashed == encrypted_password:
            print(f"User {username} authenticated successfully via system shadow")
            return True
        else:
            print(f"System authentication failed for user {username}")
            return False
            
    except PermissionError:
        print("Permission denied: Cannot read /etc/shadow. Run as root or with appropriate permissions.")
        return False
    except Exception as e:
        print(f"System authentication error: {e}")
        return False

# ==========================================
# API 路由
# ==========================================

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request'})
    
    username = data.get('username', '')
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'})
    
    # PAM 验证
    if authenticate_user(username, password):
        user = User.get_user(username)
        login_user(user, remember=remember_me)
        
        # 设置 session
        session['authenticated'] = True
        session['username'] = username
        
        # 检查是否是管理员
        is_admin = username in CONFIG.get('admin_users', ['admin'])
        session['is_admin'] = is_admin
        
        # Cookie 有效期设置
        response = jsonify({
            'success': True,
            'message': 'Login successful',
            'username': username,
            'is_admin': is_admin
        })
        
        if remember_me:
            # 设置 cookie 有效期为 7 天
            from datetime import timedelta
            response.set_cookie(
                'remember_user',
                username,
                max_age=60*60*24*7,  # 7 days
                httponly=True,
                samesite='Lax'
            )
        
        return response
    else:
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出"""
    logout_user()
    session.clear()
    
    response = jsonify({'success': True, 'message': 'Logged out successfully'})
    response.delete_cookie('remember_user')
    return response

@app.route('/api/current-user', methods=['GET'])
@require_auth
def api_current_user():
    """获取当前登录用户"""
    if session.get('authenticated'):
        return jsonify({
            'success': True,
            'data': {
                'username': session.get('username'),
                'is_admin': session.get('is_admin', False)
            }
        })
    return jsonify({'success': False, 'error': 'Not authenticated'}), 401

@app.route('/api/auth-status', methods=['GET'])
def auth_status():
    """检查认证状态（前端调用，不需要登录）"""
    if session.get('authenticated'):
        return jsonify({
            'success': True,
            'authenticated': True,
            'username': session.get('username'),
            'is_admin': session.get('is_admin', False)
        })
    else:
        # 检查 remember cookie
        username = request.cookies.get('remember_user')
        if username:
            user = User.get_user(username)
            login_user(user, remember=False)
            session['authenticated'] = True
            session['username'] = username
            is_admin = username in CONFIG.get('admin_users', ['admin'])
            session['is_admin'] = is_admin
            return jsonify({
                'success': True,
                'authenticated': True,
                'username': username,
                'is_admin': is_admin,
                'auto_login': True
            })
        return jsonify({
            'success': True,
            'authenticated': False,
            'username': None,
            'is_admin': False
        })

@app.route('/api/system-info')
@require_auth
def api_system_info():
    """获取系统信息"""
    try:
        username = session.get('username', os.environ.get('USER', os.environ.get('USERNAME', 'unknown')))
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
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'company_logo': CONFIG.get('company_logo', ''),
            'company_name': CONFIG.get('company_name', 'LSF Dashboard')
        })
    except Exception as e:
        return jsonify({'error': str(e)})

def run_lsf_command(cmd, user=None):
    """运行 LSF 命令，支持指定用户"""
    try:
        # 检查是否是管理员，如果是则强制使用 all
        is_admin = session.get('is_admin', False)
        effective_user = 'all' if is_admin else (user or session.get('username', 'all'))
        
        # 如果指定了用户（非管理员情况），添加 -u 参数
        if effective_user != 'all':
            if '-u' not in cmd:
                # 插入 -u 参数
                parts = cmd.split()
                insert_idx = 2  # bjobs/bhist 后的位置
                parts.insert(insert_idx, '-u')
                parts.insert(insert_idx + 1, effective_user)
                cmd = ' '.join(parts)
        
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = process.communicate()
        output = stdout.decode('utf-8', errors='ignore')
        error = stderr.decode('utf-8', errors='ignore')
        
        # bhist 在没有数据时返回退出码 255，但不是真正的错误
        if process.returncode != 0 and ('No matching job found' in output or 'No jobs' in output):
            return {'success': True, 'output': '', 'no_data': True}
        
        if process.returncode != 0:
            return {'success': False, 'error': error if error else 'Unknown error'}
        return {'success': True, 'output': output}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_bjobs(output, user_filter=None):
    jobs = []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return jobs
    
    # 添加 user 过滤器支持
    skip_header = True
    for line in lines[1:]:
        if not line.strip():
            continue
        
        # 过滤掉标题行
        if line.startswith('JOBID') or 'USER' in line:
            continue
            
        parts = line.split()
        if len(parts) >= 7:
            user = parts[1]
            # 应用 user 过滤器
            if user_filter and user != user_filter:
                continue
            
            jobs.append({
                'job_id': parts[0], 
                'user': user, 
                'status': parts[2],
                'queue': parts[3], 
                'host': parts[4] if len(parts) > 4 else 'N/A',
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
                'host_name': parts[0], 
                'status': parts[1],
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
                'user': parts[0], 
                'max': parts[1] if len(parts) > 1 else 'N/A',
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
                'queue_name': parts[0], 
                'status': parts[1],
                'max': parts[2] if len(parts) > 2 else 'N/A',
                'njobs': parts[3] if len(parts) > 3 else '0',
                'run': parts[4] if len(parts) > 4 else '0'
            })
    return queues

def parse_bhist(output, user_filter=None):
    """解析 bhist -w 输出，支持用户过滤"""
    jobs = []
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return jobs
    
    for line in lines[1:]:
        if not line.strip():
            continue
        # 跳过标题行
        if line.startswith('JOBID') or 'USER' in line or 'STAT' in line:
            continue
            
        parts = line.split()
        if len(parts) >= 13:
            user = parts[1]
            # 应用 user 过滤器
            if user_filter and user != user_filter:
                continue
                
            try:
                job = {
                    'bid': int(parts[0]),
                    'buser': user,
                    'status': parts[2],
                    'submitted_at': '%s %s' % (parts[3], parts[4]) if len(parts) > 4 else '',
                    'start_time': '%s %s' % (parts[5], parts[6]) if len(parts) > 6 else '',
                    'end_time': '%s %s' % (parts[7], parts[8]) if len(parts) > 8 else '',
                    'elapsed': parts[9] if len(parts) > 9 else '',
                    'command': parts[10] if len(parts) > 10 else '',
                    'partition': parts[11] if len(parts) > 11 else '',
                    'exit_code': int(parts[12]) if len(parts) > 12 and parts[12].isdigit() else 0,
                    'from_host': parts[13] if len(parts) > 13 else '',
                    'to_host': parts[14] if len(parts) > 14 else '',
                    'slots': int(parts[15]) if len(parts) > 15 and parts[15].isdigit() else 1
                }
                job['host'] = job['to_host'] or job['from_host'] or ''
                jobs.append(job)
            except (ValueError, IndexError) as e:
                continue
    return jobs

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
            loads.append({
                'host': parts[0],
                'status': parts[1] if len(parts) > 1 else 'ok',
                'r1m': float(parts[2]) if len(parts) > 2 and parts[2] != '-' else 0,
                'r15m': float(parts[3]) if len(parts) > 3 and parts[3] != '-' else 0,
                'pg': float(parts[4]) if len(parts) > 4 and parts[4] != '-' else 0,
                'ls': float(parts[6]) if len(parts) > 6 and parts[6] != '-' else 0,
                'ut': float(parts[2]) if len(parts) > 2 and parts[2] != '-' else 0
            })
    return loads

@app.route('/api/jobs')
@require_auth
def api_jobs():
    """获取作业列表，支持用户过滤"""
    user = request.args.get('user')
    if not user:
        user = session.get('username', 'all')
    
    result = run_lsf_command('bjobs -u all -w', user=user if user != 'all' else None)
    if result['success']:
        return jsonify({'success': True, 'data': parse_bjobs(result['output'], user if user != 'all' else None)})
    return jsonify(result)

@app.route('/api/hosts')
@require_auth
def api_hosts():
    result = run_lsf_command('bhosts -w')
    if result['success']:
        return jsonify({'success': True, 'data': parse_bhosts(result['output'])})
    return jsonify(result)

@app.route('/api/users')
@require_auth
def api_users():
    result = run_lsf_command('busers all -w')
    if result['success']:
        return jsonify({'success': True, 'data': parse_busers(result['output'])})
    return jsonify(result)

@app.route('/api/queues')
@require_auth
def api_queues():
    result = run_lsf_command('bqueues -w')
    if result['success']:
        return jsonify({'success': True, 'data': parse_bqueues(result['output'])})
    return jsonify(result)

@app.route('/api/load')
@require_auth
def api_load():
    result = run_lsf_command('lsload -w')
    if result['success']:
        return jsonify({'success': True, 'data': parse_lsload(result['output'])})
    return jsonify(result)

@app.route('/api/job/<job_id>')
@require_auth
def api_job_detail(job_id):
    """获取作业详情，支持指定用户"""
    user = session.get('username')
    result = run_lsf_command('bjobs -l %s' % job_id, user=user)
    if result['success']:
        return jsonify({'success': True, 'data': result['output']})
    return jsonify(result)

@app.route('/api/kill/<job_id>', methods=['POST'])
@require_auth
def api_kill_job(job_id):
    """终止作业，支持指定用户"""
    user = session.get('username')
    result = run_lsf_command('bkill %s' % job_id, user=user)
    return jsonify(result)

@app.route('/api/load-trend')
@require_auth
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
# 用户配置 API
# ==========================================

@app.route('/api/user/profile', methods=['GET'])
@require_auth
def api_get_user_profile():
    """获取用户配置"""
    try:
        username = session.get('username')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_profiles WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            profile = {
                'username': row['username'],
                'display_name': row['display_name'] or username,
                'email': row['email'] or '',
                'theme': row['theme'] or 'light',
                'language': row['language'] or 'zh-CN'
            }
        else:
            profile = {
                'username': username,
                'display_name': username,
                'email': '',
                'theme': 'light',
                'language': 'zh-CN'
            }
        
        return jsonify({'success': True, 'data': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/user/profile', methods=['PUT'])
@require_auth
def api_update_user_profile():
    """更新用户配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request'})
        
        username = session.get('username')
        display_name = data.get('display_name', username)
        email = data.get('email', '')
        theme = data.get('theme', 'light')
        language = data.get('language', 'zh-CN')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute('SELECT username FROM user_profiles WHERE username = ?', (username,))
        existing = cursor.fetchone()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing:
            cursor.execute('''
                UPDATE user_profiles SET
                    display_name = ?, email = ?, theme = ?, language = ?,
                    updated_at = ?
                WHERE username = ?
            ''', (display_name, email, theme, language, current_time, username))
        else:
            cursor.execute('''
                INSERT INTO user_profiles 
                (username, display_name, email, theme, language, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, display_name, email, theme, language, current_time, current_time))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'username': username,
                'display_name': display_name,
                'email': email,
                'theme': theme,
                'language': language
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==========================================
# 管理员配置 API
# ==========================================

@app.route('/api/admin/config', methods=['GET'])
@require_auth
@require_admin
def api_get_admin_config():
    """获取管理员配置"""
    return jsonify({
        'success': True,
        'data': {
            'admin_users': CONFIG.get('admin_users', ['admin']),
            'company_logo': CONFIG.get('company_logo', ''),
            'company_name': CONFIG.get('company_name', 'LSF Dashboard')
        }
    })

@app.route('/api/admin/config', methods=['PUT'])
@require_auth
@require_admin
def api_update_admin_config():
    """更新管理员配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request'})
        
        # 更新配置
        CONFIG['admin_users'] = data.get('admin_users', CONFIG.get('admin_users', ['admin']))
        CONFIG['company_logo'] = data.get('company_logo', CONFIG.get('company_logo', ''))
        CONFIG['company_name'] = data.get('company_name', CONFIG.get('company_name', 'LSF Dashboard'))
        
        # 保存到文件
        save_config(CONFIG)
        
        return jsonify({
            'success': True,
            'data': {
                'admin_users': CONFIG['admin_users'],
                'company_logo': CONFIG['company_logo'],
                'company_name': CONFIG['company_name']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/change-password', methods=['POST'])
@require_auth
@require_admin
def api_change_admin_password():
    """修改管理员密码（需要系统权限）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request'})
        
        username = session.get('username')
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'success': False, 'error': 'Password required'})
        
        # 验证旧密码
        if not authenticate_user(username, old_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        # 修改密码（这需要系统权限，通常需要root）
        try:
            import subprocess
            # 使用 chpasswd 命令修改密码
            cmd = f'echo "{username}:{new_password}" | sudo chpasswd'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return jsonify({'success': True, 'message': 'Password changed successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to change password. Check system permissions.'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'Password change failed: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==========================================
# 管理员后台 API
# ==========================================

@app.route('/api/history/jobs', methods=['GET'])
@require_auth
def api_history_jobs():
    """分页获取历史作业，支持按用户过滤"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        user_filter = request.args.get('user', '')
        
        # 管理员可以看到所有用户的数据，普通用户只能看到自己的
        current_user = session.get('username')
        is_admin = session.get('is_admin', False)
        
        if not is_admin and user_filter and user_filter != current_user:
            return jsonify({'success': False, 'error': 'Access denied'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 计算总数
        if user_filter:
            cursor.execute('SELECT COUNT(*) FROM job_history WHERE buser = ?', (user_filter,))
        elif not is_admin:
            cursor.execute('SELECT COUNT(*) FROM job_history WHERE buser = ?', (current_user,))
        else:
            cursor.execute('SELECT COUNT(*) FROM job_history')
        total = cursor.fetchone()[0]
        
        # 查询数据
        offset = (page - 1) * page_size
        if user_filter:
            cursor.execute('''
                SELECT * FROM job_history 
                WHERE buser = ? 
                ORDER BY submitted_at DESC 
                LIMIT ? OFFSET ?
            ''', (user_filter, page_size, offset))
        elif not is_admin:
            cursor.execute('''
                SELECT * FROM job_history 
                WHERE buser = ?
                ORDER BY submitted_at DESC 
                LIMIT ? OFFSET ?
            ''', (current_user, page_size, offset))
        else:
            cursor.execute('''
                SELECT * FROM job_history 
                ORDER BY submitted_at DESC 
                LIMIT ? OFFSET ?
            ''', (page_size, offset))
        
        rows = cursor.fetchall()
        jobs = []
        for row in rows:
            jobs.append({
                'bid': row['bid'],
                'buser': row['buser'],
                'command': row['command'],
                'status': row['status'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'host': row['host'],
                'slots': row['slots'],
                'count': row['count'],
                'exit_code': row['exit_code'],
                'submitted_at': row['submitted_at'],
                'created_at': row['created_at']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'jobs': jobs,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history/job/<int:bid>', methods=['GET'])
@require_auth
def api_history_job_detail(bid):
    """获取单个作业详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM job_history WHERE bid = ?', (bid,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # 检查权限：管理员可以看所有，普通用户只能看自己的
            current_user = session.get('username')
            is_admin = session.get('is_admin', False)
            if not is_admin and row['buser'] != current_user:
                return jsonify({'success': False, 'error': 'Access denied'})
            
            return jsonify({
                'success': True,
                'data': {
                    'bid': row['bid'],
                    'buser': row['buser'],
                    'command': row['command'],
                    'status': row['status'],
                    'start_time': row['start_time'],
                    'end_time': row['end_time'],
                    'host': row['host'],
                    'slots': row['slots'],
                    'count': row['count'],
                    'exit_code': row['exit_code'],
                    'submitted_at': row['submitted_at'],
                    'created_at': row['created_at']
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Job not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history/import', methods=['POST'])
@require_auth
def api_history_import():
    """导入 bhist 数据"""
    try:
        user = session.get('username', 'all')
        result = run_lsf_command('bhist -a -w', user=user if user != 'all' else None)
        if not result['success']:
            return jsonify({'success': False, 'error': result['error']})
        
        jobs = parse_bhist(result['output'], user if user != 'all' else None)
        if not jobs:
            return jsonify({'success': True, 'message': 'No jobs to import', 'imported': 0})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(bid) FROM job_history')
        max_bid_row = cursor.fetchone()
        max_bid = max_bid_row[0] if max_bid_row and max_bid_row[0] else 0
        
        imported_count = 0
        updated_count = 0
        
        for job in jobs:
            if job['bid'] > max_bid:
                try:
                    cursor.execute('''
                        INSERT INTO job_history 
                        (bid, buser, command, status, start_time, end_time, host, slots, exit_code, submitted_at, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job['bid'], job['buser'], job['command'], job['status'],
                        job['start_time'], job['end_time'], job['host'],
                        job['slots'], job['exit_code'], job['submitted_at'],
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    imported_count += 1
                except sqlite3.IntegrityError:
                    cursor.execute('''
                        UPDATE job_history SET
                            buser = ?, command = ?, status = ?,
                            start_time = ?, end_time = ?, host = ?,
                            slots = ?, exit_code = ?, submitted_at = ?
                        WHERE bid = ?
                    ''', (
                        job['buser'], job['command'], job['status'],
                        job['start_time'], job['end_time'], job['host'],
                        job['slots'], job['exit_code'], job['submitted_at'], job['bid']
                    ))
                    updated_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Import completed',
            'imported': imported_count,
            'updated': updated_count,
            'total_processed': len(jobs)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history/stats/slots', methods=['GET'])
@require_auth
def api_history_slots_stats():
    """获取 slots 使用趋势"""
    try:
        period = request.args.get('period', 'day')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 普通用户只能看自己的数据
        current_user = session.get('username')
        is_admin = session.get('is_admin', False)
        
        if period == 'day':
            if is_admin:
                sql = '''
                    SELECT 
                        strftime('%Y-%m-%d %H', submitted_at) as time_bucket,
                        SUM(slots) as total_slots,
                        COUNT(*) as job_count
                    FROM job_history
                    WHERE submitted_at >= datetime('now', '-24 hours')
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                '''
            else:
                sql = '''
                    SELECT 
                        strftime('%Y-%m-%d %H', submitted_at) as time_bucket,
                        SUM(slots) as total_slots,
                        COUNT(*) as job_count
                    FROM job_history
                    WHERE submitted_at >= datetime('now', '-24 hours')
                    AND buser = ?
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                '''
                cursor.execute(sql, (current_user,))
                rows = cursor.fetchall()
                conn.close()
                
                trend_data = []
                for row in rows:
                    trend_data.append({
                        'time': row['time_bucket'],
                        'slots': row['total_slots'] or 0,
                        'job_count': row['job_count'] or 0
                    })
                return jsonify({'success': True, 'data': trend_data})
        elif period == 'week':
            if is_admin:
                sql = '''
                    SELECT 
                        strftime('%Y-%m-%d', submitted_at) as time_bucket,
                        SUM(slots) as total_slots,
                        COUNT(*) as job_count
                    FROM job_history
                    WHERE submitted_at >= datetime('now', '-7 days')
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                '''
            else:
                sql = '''
                    SELECT 
                        strftime('%Y-%m-%d', submitted_at) as time_bucket,
                        SUM(slots) as total_slots,
                        COUNT(*) as job_count
                    FROM job_history
                    WHERE submitted_at >= datetime('now', '-7 days')
                    AND buser = ?
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                '''
                cursor.execute(sql, (current_user,))
                rows = cursor.fetchall()
                conn.close()
                
                trend_data = []
                for row in rows:
                    trend_data.append({
                        'time': row['time_bucket'],
                        'slots': row['total_slots'] or 0,
                        'job_count': row['job_count'] or 0
                    })
                return jsonify({'success': True, 'data': trend_data})
        else:
            if is_admin:
                sql = '''
                    SELECT 
                        strftime('%Y-%m-%d', submitted_at) as time_bucket,
                        SUM(slots) as total_slots,
                        COUNT(*) as job_count
                    FROM job_history
                    WHERE submitted_at >= datetime('now', '-30 days')
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                '''
            else:
                sql = '''
                    SELECT 
                        strftime('%Y-%m-%d', submitted_at) as time_bucket,
                        SUM(slots) as total_slots,
                        COUNT(*) as job_count
                    FROM job_history
                    WHERE submitted_at >= datetime('now', '-30 days')
                    AND buser = ?
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                '''
                cursor.execute(sql, (current_user,))
                rows = cursor.fetchall()
                conn.close()
                
                trend_data = []
                for row in rows:
                    trend_data.append({
                        'time': row['time_bucket'],
                        'slots': row['total_slots'] or 0,
                        'job_count': row['job_count'] or 0
                    })
                return jsonify({'success': True, 'data': trend_data})
        
        # 管理员执行
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        
        trend_data = []
        for row in rows:
            trend_data.append({
                'time': row['time_bucket'],
                'slots': row['total_slots'] or 0,
                'job_count': row['job_count'] or 0
            })
        
        return jsonify({'success': True, 'data': trend_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==========================================
# 登录页面路由
# ==========================================

@app.route('/login')
def login_page():
    """登录页面"""
    return send_from_directory(FRONTEND_DIST, 'index.html')

@app.route('/auth')
def auth_page():
    """认证页面（备用）"""
    return send_from_directory(FRONTEND_DIST, 'index.html')

# ==========================================
# 前端静态文件路由
# ==========================================

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """提供前端 JS/CSS 等静态资源"""
    return send_from_directory(ASSETS_DIR, filename)

@app.route('/')
def index():
    """返回首页"""
    return send_from_directory(FRONTEND_DIST, 'index.html')

# 捕获所有前端路由，返回 index.html（SPA fallback）
@app.route('/<path:path>')
def serve_spa(path):
    """处理 Vue Router 的前端路由"""
    # 如果是 API 或 assets 路由，不应该到这里
    if path.startswith('api/') or path.startswith('assets/'):
        return jsonify({'error': 'Not Found'}), 404
    return send_from_directory(FRONTEND_DIST, 'index.html')

if __name__ == '__main__':
    print("Starting LSF Dashboard Server with System Authentication...")
    print("Access at: http://localhost:5002")
    print("Authentication: System-level (/etc/shadow)")
    print("Use any local system account to login")
    app.run(host='0.0.0.0', port=5002, debug=False)