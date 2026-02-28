
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from init_data import init_database

def reset_and_init():
    app = create_app()
    with app.app_context():
        print("⚠️ 正在清空旧数据 (Dropping all tables)...")
        db.drop_all()
        print("✓ 旧数据已清空")
        
        print("🔄 开始重新初始化数据 (Running initialization)...")
        # init_database 会重新建表并插入数据
        # 因为表已空，它不会跳过
        init_database()

if __name__ == "__main__":
    confirm = input("❗此操作将清空所有数据并重置为初始状态。确认请输入 'y': ")
    if confirm.lower() == 'y':
        reset_and_init()
    else:
        print("操作已取消")
