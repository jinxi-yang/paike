
import requests
import json
import time
import os

YEAR = 2026
OUTPUT_FILE = f"holidays_{YEAR}.json"
API_URL = f"https://timor.tech/api/holiday/year/{YEAR}"

def fetch_holidays():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Fetching holidays for {YEAR} from {API_URL}...")
    
    for attempt in range(5):
        try:
            resp = requests.get(API_URL, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 0:
                    holiday_map = data.get('holiday', {})
                    # Save to file
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(holiday_map, f, ensure_ascii=False, indent=2)
                    print(f"Successfully saved {len(holiday_map)} holiday records to {OUTPUT_FILE}")
                    return True
            print(f"Attempt {attempt+1} failed: Status {resp.status_code}")
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        
        time.sleep(2)
    
    return False

if __name__ == "__main__":
    if fetch_holidays():
        print("Done.")
    else:
        print("Failed to fetch holidays.")
