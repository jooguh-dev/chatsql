#!/usr/bin/env python
"""
直接测试Anthropic API连接
"""
import os
from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic

def test_anthropic_connection():
    """直接测试Anthropic API连接"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ ANTHROPIC_API_KEY 未配置")
        return False
    
    print("=" * 80)
    print("直接测试Anthropic API连接")
    print("=" * 80)
    print(f"\nAPI Key 前缀: {api_key[:20]}...")
    print(f"API Key 长度: {len(api_key)}")
    print(f"模型: claude-3-haiku-20240307")
    
    try:
        client = Anthropic(api_key=api_key)
        
        print("\n发送测试请求...")
        response = client.messages.create(
            model='claude-3-haiku-20240307',
            max_tokens=50,
            temperature=0.3,
            messages=[
                {"role": "user", "content": "What is SQL? Answer in one sentence."}
            ]
        )
        
        if response.content:
            result = response.content[0].text.strip()
            print("\n✅ Anthropic API连接成功!")
            print(f"\n响应内容: {result}")
            return True
        else:
            print("\n❌ Anthropic API返回空响应")
            return False
            
    except Exception as e:
        print(f"\n❌ Anthropic API调用失败: {e}")
        error_str = str(e)
        
        if "429" in error_str or "quota" in error_str.lower() or "rate_limit" in error_str.lower():
            print("\n⚠️  错误类型: API配额不足或速率限制")
            print("   请检查Anthropic账户余额和配额限制")
            print("   访问: https://console.anthropic.com/")
        elif "401" in error_str or "unauthorized" in error_str.lower() or "authentication" in error_str.lower():
            print("\n⚠️  错误类型: API密钥无效")
            print("   请检查API密钥是否正确")
            print("   访问: https://console.anthropic.com/settings/keys")
        elif "invalid" in error_str.lower():
            print("\n⚠️  错误类型: API密钥格式无效")
            print("   请确认API密钥格式正确（应以sk-ant-开头）")
        else:
            print(f"\n⚠️  其他错误: {error_str}")
        
        return False

if __name__ == '__main__':
    success = test_anthropic_connection()
    if success:
        print("\n🎉 Anthropic API工作正常！")
    else:
        print("\n⚠️  Anthropic API连接失败，请检查配置和账户状态。")
    exit(0 if success else 1)

