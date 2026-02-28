
import requests
import json

url = "https://timor.tech/api/holiday/info/2026-05-02"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    print(f"Requesting {url}...")
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Content Type: {resp.headers.get('Content-Type')}")
    print(f"Text Preview: {resp.text[:500]}")
    
    data = resp.json()
    print("JSON Data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
