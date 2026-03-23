"""
Flask主应用 - 北清商学院排课系统
"""
from flask import Flask, jsonify, send_file, make_response, session, request
from flask_cors import CORS
from config import Config
from models import db
import os
import logging

# 配置日志 - 确保控制台能看到所有日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def create_app():
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    
    # 前端页面路由（直接从 Flask 提供，确保最新版本）
    _frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
    
    @app.route('/')
    def serve_frontend():
        resp = make_response(send_file(os.path.join(_frontend_dir, 'index.html')))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    
    # ======== 认证与权限中间件 ========
    @app.before_request
    def check_auth():
        path = request.path
        method = request.method

        # 白名单：前端页面、认证接口、健康检查、静态资源
        if path == '/' or path.startswith('/api/auth') or path == '/api/health':
            return None

        # 所有 /api/* 请求需要登录
        if path.startswith('/api/'):
            if 'username' not in session:
                return jsonify({'error': '未登录，请先登录'}), 401

            # viewer 角色禁止写操作
            if session.get('role') == 'viewer' and method in ('POST', 'PUT', 'DELETE'):
                return jsonify({'error': '当前账号仅有查看权限，无法执行此操作'}), 403

        return None

    # 注册蓝图
    from routes import (
        project_bp,
        topic_bp,
        homeroom_bp,
        teacher_bp,
        course_bp,
        combo_bp,
        classes_bp,
        schedule_bp,
        ai_bp,
        init_bp,
        auth_bp
    )
    
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(topic_bp, url_prefix='/api/topics')
    app.register_blueprint(homeroom_bp, url_prefix='/api/homerooms')
    app.register_blueprint(teacher_bp, url_prefix='/api/teachers')
    app.register_blueprint(course_bp, url_prefix='/api/courses')
    app.register_blueprint(combo_bp, url_prefix='/api/combos')
    app.register_blueprint(classes_bp, url_prefix='/api/classes')
    app.register_blueprint(schedule_bp, url_prefix='/api/schedule')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(init_bp, url_prefix='/api/init')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # 健康检查
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'message': '北清商学院排课系统运行中'})
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found'}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal Server Error'}), 500
    
    # 创建所有表（如果不存在）— 兼容 gunicorn / python app.py 两种启动方式
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == '__main__':
    import signal
    import sys

    def _graceful_exit(signum, frame):
        print('\n⏹️  收到停止信号，正在关闭...')
        sys.exit(0)

    signal.signal(signal.SIGINT, _graceful_exit)
    signal.signal(signal.SIGTERM, _graceful_exit)
    app.run(host='0.0.0.0', port=5000, debug=True)
