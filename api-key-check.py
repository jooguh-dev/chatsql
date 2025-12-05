import requests
import os


api_key = os.getenv("ANTHROPIC_API_KEY", "")


headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

# 测试 API key 是否有效
url = "https://api.anthropic.com/v1/messages"
data = {
    "model": "claude-3-haiku-20240307",  # 或者使用其他可用模型
    "max_tokens": 10,
    "messages": [
        {"role": "user", "content": "Hi"}
    ]
}

try:
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    print("状态码:", response.status_code)
    print("响应内容:", result)
    
    if response.status_code == 200:
        print("\n✓ API key 有效且可以正常使用")
    elif response.status_code == 401:
        print("\n✗ API key 无效或未授权")
    elif response.status_code == 404:
        print("\n✗ 模型不存在或你的账户没有访问权限")
        print("尝试使用其他模型，如: claude-3-haiku-20240307")
    elif response.status_code == 429:
        print("\n✗ 请求过于频繁或配额不足")
    else:
        print(f"\n✗ 发生错误: {result.get('error', {}).get('message', '未知错误')}")
        
except Exception as e:
    print(f"请求失败: {e}")