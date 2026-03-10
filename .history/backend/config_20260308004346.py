"""
配置文件 - 北清商学院排课系统
"""
import os

class Config:
    # 数据库配置 - 使用SQLite（无需部署数据库服务）
    _db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'scheduler.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{_db_path}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设为True可查看SQL语句
    
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'beiqing-scheduler-secret-key-2026')
    JSON_AS_ASCII = False  # 支持中文JSON响应
    
    # 节假日API
    HOLIDAY_API_BASE = 'https://timor.tech/api/holiday'
    
    # AI智能体接口（预留）
    AI_AGENT_URL = os.environ.get('AI_AGENT_URL', 'https://ai.isstech.com/agent/v1/chat-messages')
    AI_AGENT_API_KEY = os.environ.get('AI_AGENT_API_KEY', 'app-FgzMYQKCT5T8Shh1LPFySOjL')
    
    # 排课配置
    MIN_WEEKS_INTERVAL = 4  # 最小排课间隔（周）
    MAX_WEEKS_INTERVAL = 5  # 最大排课间隔（周）
