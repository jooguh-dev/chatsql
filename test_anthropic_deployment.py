#!/usr/bin/env python
"""
测试Anthropic AI部署是否正常工作
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatsql.settings')
django.setup()

from django.conf import settings
from ai_tutor.services.openai_service import get_ai_response

def test_anthropic_configuration():
    """测试Anthropic配置"""
    print("=" * 80)
    print("Anthropic AI部署配置检查")
    print("=" * 80)
    
    # 检查配置
    anthropic_mode = getattr(settings, 'ANTHROPIC_MODE', 'mock')
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    print(f"\n1. ANTHROPIC_MODE: {anthropic_mode}")
    print(f"2. ANTHROPIC_API_KEY: {'已配置' if api_key else '未配置'}")
    if api_key:
        print(f"   API Key 前缀: {api_key[:20]}...")
    
    if anthropic_mode != 'real':
        print("\n⚠️  警告: ANTHROPIC_MODE 不是 'real'，AI将使用mock模式")
        print("   请在 .env 文件中设置: ANTHROPIC_MODE=real")
        return False
    
    if not api_key:
        print("\n❌ 错误: ANTHROPIC_API_KEY 未配置")
        print("   请在 .env 文件中设置: ANTHROPIC_API_KEY=your_key_here")
        return False
    
    print("\n✅ 配置检查通过")
    return True


def test_ai_response():
    """测试AI响应"""
    print("\n" + "=" * 80)
    print("测试AI响应")
    print("=" * 80)
    
    # 创建一个模拟的exercise对象
    class MockExercise:
        def __init__(self):
            self.id = 1
            self.title = "Test Problem"
            self.description = "This is a test problem description"
            self.difficulty = "easy"
    
    exercise = MockExercise()
    
    # 测试消息
    test_message = "What is SQL?"
    
    print(f"\n发送测试消息: '{test_message}'")
    print("等待AI响应...\n")
    
    try:
        result = get_ai_response(
            message=test_message,
            exercise=exercise,
            user_query=None,
            error=None,
            user_role='student',
            user_id=1,
            submissions=[]
        )
        
        print("✅ AI响应成功!")
        print(f"\n响应内容:")
        print("-" * 80)
        print(result.get('response', 'No response'))
        print("-" * 80)
        
        print(f"\n响应详情:")
        print(f"  - Intent: {result.get('intent', 'N/A')}")
        print(f"  - SQL Query: {result.get('sql_query', 'None')}")
        print(f"  - Should Execute: {result.get('should_execute', False)}")
        
        if result.get('intent') == 'error':
            print("\n❌ AI返回错误状态")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ AI调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_with_submissions():
    """测试AI处理submissions的能力"""
    print("\n" + "=" * 80)
    print("测试AI处理Submissions")
    print("=" * 80)
    
    class MockExercise:
        def __init__(self):
            self.id = 1
            self.title = "Find Employees"
            self.description = "Find all employees in the Engineering department"
            self.difficulty = "easy"
    
    exercise = MockExercise()
    
    # 模拟submissions
    submissions = [
        {
            'id': 1,
            'query': 'SELECT * FROM employees WHERE dept = "Engineering"',
            'status': 'incorrect',
            'created_at': '2024-12-01T10:00:00Z'
        },
        {
            'id': 2,
            'query': 'SELECT name, dept FROM employees WHERE dept = "Engineering"',
            'status': 'correct',
            'created_at': '2024-12-01T11:00:00Z'
        }
    ]
    
    test_message = "I had an incorrect submission earlier. Can you help me understand what went wrong?"
    
    print(f"\n发送测试消息: '{test_message}'")
    print(f"Submissions数量: {len(submissions)}")
    print("等待AI响应...\n")
    
    try:
        result = get_ai_response(
            message=test_message,
            exercise=exercise,
            user_query=None,
            error=None,
            user_role='student',
            user_id=1,
            submissions=submissions
        )
        
        print("✅ AI响应成功!")
        print(f"\n响应内容:")
        print("-" * 80)
        print(result.get('response', 'No response')[:500])  # 只显示前500字符
        print("-" * 80)
        
        # 检查响应是否提到了submissions
        response_text = result.get('response', '').lower()
        if 'submission' in response_text or 'incorrect' in response_text or 'query' in response_text:
            print("\n✅ AI成功识别并引用了submissions历史")
        else:
            print("\n⚠️  AI响应可能没有引用submissions历史")
        
        return True
        
    except Exception as e:
        print(f"\n❌ AI调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Anthropic AI部署测试脚本")
    print("=" * 80)
    
    # 1. 检查配置
    config_ok = test_anthropic_configuration()
    
    if not config_ok:
        print("\n❌ 配置检查失败，请先修复配置问题")
        sys.exit(1)
    
    # 2. 测试基本AI响应
    print("\n")
    basic_test_ok = test_ai_response()
    
    # 3. 测试AI处理submissions
    print("\n")
    submissions_test_ok = test_ai_with_submissions()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"配置检查: {'✅ 通过' if config_ok else '❌ 失败'}")
    print(f"基本AI测试: {'✅ 通过' if basic_test_ok else '❌ 失败'}")
    print(f"Submissions测试: {'✅ 通过' if submissions_test_ok else '❌ 失败'}")
    
    if config_ok and basic_test_ok and submissions_test_ok:
        print("\n🎉 所有测试通过！Anthropic AI已正确部署。")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查配置和日志。")
        sys.exit(1)

