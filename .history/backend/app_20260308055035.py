"""
Flask主应用 - 北清商学院排课系统
"""
from flask import Flask, jsonify, send_file, make_response
from flask_cors import CORS
from config import Config
from models import db
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 前端页面路由（直接从 Flask 提供，确保最新版本）
    _frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
    
    @app.route('/')
    def serve_frontend():
        resp = make_response(send_file(os.path.join(_frontend_dir, 'index.html')))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    
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
        init_bp
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
    
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # 创建所有表（如果不存在）
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
