
import sys
import os
import json
from flask import Flask, jsonify

# Ensure we can import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from routes.ai import extract_constraints
except ImportError:
    print("Failed to import extract_constraints")
    sys.exit(1)

# Mock Flask app and request context
app = Flask(__name__)

def test_empty_prompt():
    print("=== Testing Empty Prompt Handling ===")
    with app.test_request_context(
        '/ai/extract-constraints',
        method='POST',
        json={'prompt': '', 'context': {}}
    ):
        try:
            # Call the function directly (it uses request.get_json())
            response = extract_constraints()
            
            # extract_constraints returns a Response object (jsonify)
            data = response.get_json()
            
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if 'constraints' in data and data['constraints'] == {}:
                print("PASS: Returned empty constraints for empty prompt.")
            else:
                print("FAIL: Did not return empty constraints.")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_empty_prompt()
