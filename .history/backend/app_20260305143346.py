"""
Flask主应用 - 北清商学院排课系统
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
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
        ai_bp
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
