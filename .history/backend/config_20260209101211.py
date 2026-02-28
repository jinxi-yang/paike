"""
配置文件 - 北清商学院排课系统
"""
import os

class Config:
    # MySQL数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '10.156.195.35')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '112233')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'bqsxy')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设为True可查看SQL语句
    
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'beiqing-scheduler-secret-key-2026')
    JSON_AS_ASCII = False  # 支持中文JSON响应
    
    # 节假日API
    HOLIDAY_API_BASE = 'https://timor.tech/api/holiday'
    
    # AI智能体接口（预留）
    AI_AGENT_URL = os.environ.get('AI_AGENT_URL', 'https://ai.isstech.com/agent/v1')
    AI_AGENT_API_KEY = os.environ.get('AI_AGENT_API_KEY', 'app-FgzMYQKCT5T8Shh1LPFySOjL')
    
    # 排课配置
    MIN_WEEKS_INTERVAL = 4  # 最小排课间隔（周）
    MAX_WEEKS_INTERVAL = 5  # 最大排课间隔（周）
