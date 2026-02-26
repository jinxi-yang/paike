
import sys
import os
import json
import requests
from config import Config

# Ensure key is present (loaded from config.py)

def test_dify_call():
    print("=== Testing Dify API Call ===")
    
    ai_url = Config.AI_AGENT_URL
    api_key = Config.AI_AGENT_API_KEY
    
    print(f"URL: {ai_url}")
    print(f"Key: {api_key[:5]}******")
    
    prompt = "班主任李婷婷4月12日请假"
    context = {
        "current_month": "2026-04",
        "classes": ["领袖班1期", "医疗班2期"],
        "teachers": ["王老师", "李婷婷"]
    }
    
    # 构造组合Prompt (Current Logic)
    full_query = f"""
    【用户指令】
    {prompt}

    【当前排课上下文】
    当前月份: {context.get('current_month')}
    活跃班级: {', '.join(context.get('classes', []))}
    讲师名单: {', '.join(context.get('teachers', []))}

    请根据上述信息提取排课约束，Strictly return VALID JSON ONLY.
    """
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Payload similar to current implementation
    payload = {
        "inputs": {}, # Empty inputs currently
        "query": full_query,
        "response_mode": "blocking",
        "conversation_id": "",
        "user": "debug-user"
    }
    
    print("\nSending Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        resp = requests.post(ai_url, json=payload, headers=headers, timeout=30)
        print(f"\nStatus Code: {resp.status_code}")
        print("Response Body:")
        print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dify_call()
