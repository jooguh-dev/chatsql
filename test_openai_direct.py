#!/usr/bin/env python
"""
直接测试OpenAI API连接
"""
import os
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

def test_openai_connection():
    """直接测试OpenAI API连接"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY 未配置")
        return False
    
    print("=" * 80)
    print("直接测试OpenAI API连接")
    print("=" * 80)
    print(f"\nAPI Key 前缀: {api_key[:20]}...")
    print(f"API Key 长度: {len(api_key)}")
    
    try:
        client = OpenAI(api_key=api_key)
        
        print("\n发送测试请求...")
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {"role": "system", "content": "You are a helpful SQL tutor."},
                {"role": "user", "content": "What is SQL? Answer in one sentence."}
            ],
            max_tokens=50,
            temperature=0.3,
        )
        
        if response.choices:
            result = response.choices[0].message.content.strip()
            print("\n✅ OpenAI API连接成功!")
            print(f"\n响应内容: {result}")
            return True
        else:
            print("\n❌ OpenAI API返回空响应")
            return False
            
    except Exception as e:
        print(f"\n❌ OpenAI API调用失败: {e}")
        error_str = str(e)
        
        if "429" in error_str or "quota" in error_str.lower():
            print("\n⚠️  错误类型: API配额不足")
            print("   请检查OpenAI账户余额和配额限制")
            print("   访问: https://platform.openai.com/account/billing")
        elif "401" in error_str or "unauthorized" in error_str.lower():
            print("\n⚠️  错误类型: API密钥无效")
            print("   请检查API密钥是否正确")
        elif "invalid" in error_str.lower():
            print("\n⚠️  错误类型: API密钥格式无效")
            print("   请确认API密钥格式正确")
        else:
            print(f"\n⚠️  其他错误: {error_str}")
        
        return False

if __name__ == '__main__':
    success = test_openai_connection()
    if success:
        print("\n🎉 OpenAI API工作正常！")
    else:
        print("\n⚠️  OpenAI API连接失败，请检查配置和账户状态。")
    exit(0 if success else 1)

