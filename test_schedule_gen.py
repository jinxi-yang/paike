import os
import sys

# Add backend directory to sys.path so imports work
backend_dir = os.path.abspath(r"d:\学习\outputmsg\排课\paike\backend")
sys.path.insert(0, backend_dir)

from app import app
from models import db, Class, TeacherCourseCombo, Topic
from routes.schedule import _run_best_of_n

with app.app_context():
    try:
        # Just run a tiny dry-run to see if any .course exceptions are thrown
        print("Starting _run_best_of_n dry run...", flush=True)
        assignments, quality = _run_best_of_n(2026, 4, constraints={}, n_rounds=1, conflict_mode='smart')
        print("SUCCESS! No exceptions thrown.")
        print(f"Generated {len(assignments)} assignments.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("FAILED with Exception!")
