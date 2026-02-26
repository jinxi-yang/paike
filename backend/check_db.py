
import sys
import os
import time

# Ensure we can import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db

def check_db_connection():
    app = create_app()
    with app.app_context():
        print("Pinging DB...")
        try:
            # Simple query to check connection
            start_time = time.time()
            db.session.execute(db.text("SELECT 1"))
            end_time = time.time()
            print(f"DB Connection OK! Latency: {end_time - start_time:.4f}s")
            
            # Check table existence (metadata)
            print("Checking tables...")
            engine = db.engine
            inspector = db.inspect(engine)
            tables = inspector.get_table_names()
            print(f"Tables found: {tables}")
            
        except Exception as e:
            print(f"DB Error: {e}")

if __name__ == "__main__":
    check_db_connection()
