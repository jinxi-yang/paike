"""
认证API - 登录/登出/当前用户
"""
from flask import Blueprint, jsonify, request, session

auth_bp = Blueprint('auth', __name__)

# 硬编码账号（admin=全权限, viewer=仅查看）
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'display': '管理员'},
    'viewer': {'password': 'viewer123', 'role': 'viewer', 'display': '查看者'},
}


@auth_bp.route('/login', methods=['POST'])
def login():
    """登录"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = USERS.get(username)
    if not user or user['password'] != password:
        return jsonify({'error': '用户名或密码错误'}), 401

    session['username'] = username
    session['role'] = user['role']
    return jsonify({
        'username': username,
        'role': user['role'],
        'display': user['display']
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """登出"""
    session.clear()
    return jsonify({'message': '已登出'})


@auth_bp.route('/me', methods=['GET'])
def me():
    """获取当前登录用户"""
    username = session.get('username')
    if not username:
        return jsonify({'error': '未登录'}), 401
    user = USERS.get(username, {})
    return jsonify({
        'username': username,
        'role': session.get('role', 'viewer'),
        'display': user.get('display', username)
    })
