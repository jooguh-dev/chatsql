#!/usr/bin/env python
"""
测试浏览器session - 模拟浏览器请求
"""

import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatsql.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Django设置失败: {e}")
    sys.exit(1)

from django.contrib.sessions.models import Session
from django.utils import timezone
from exercises.views import SubmissionListView
from django.test import RequestFactory


def find_test1_session():
    """查找test1的活跃session"""
    print("=" * 80)
    print("查找test1 (user_id=1) 的活跃session")
    print("=" * 80)
    
    sessions = Session.objects.filter(
        expire_date__gt=timezone.now()
    ).order_by('-expire_date')
    
    test1_sessions = []
    for session in sessions:
        try:
            session_data = session.get_decoded()
            if session_data.get('user_id') == 1 and session_data.get('username') == 'test1':
                test1_sessions.append(session)
        except:
            pass
    
    if not test1_sessions:
        print("❌ 没有找到test1的活跃session")
        print("   请确保在浏览器中已登录test1")
        return None
    
    print(f"✅ 找到 {len(test1_sessions)} 个test1的活跃session")
    latest = test1_sessions[0]
    print(f"   最新的session key: {latest.session_key}")
    print(f"   过期时间: {latest.expire_date}")
    
    return latest


def test_submissions_api(session):
    """使用test1的session测试API"""
    print("\n" + "=" * 80)
    print("测试Submissions API（使用test1的session）")
    print("=" * 80)
    
    # 获取exercise_id=1的提交记录
    exercise_id = 1
    
    factory = RequestFactory()
    request = factory.get(f'/api/exercises/{exercise_id}/submissions/')
    
    # 设置session
    request.session = session
    
    # 调用API
    view = SubmissionListView()
    try:
        response = view.get(request, exercise_id=exercise_id)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            submissions = response.data
            print(f"✅ 成功获取 {len(submissions)} 条提交记录")
            if submissions:
                for i, sub in enumerate(submissions, 1):
                    print(f"\n   提交 #{i}:")
                    print(f"     ID: {sub['id']}")
                    print(f"     状态: {sub['status']}")
                    print(f"     查询: {sub['query'][:50]}...")
                    print(f"     执行时间: {sub['execution_time']}")
                    print(f"     创建时间: {sub['created_at']}")
            else:
                print("   ⚠️  没有找到提交记录")
        else:
            print(f"❌ API返回错误: {response.data}")
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()


def show_browser_instructions(session_key):
    """显示浏览器检查指令"""
    print("\n" + "=" * 80)
    print("浏览器检查指令")
    print("=" * 80)
    print(f"\n你的session key应该是: {session_key}")
    print("\n请在浏览器中检查:")
    print("1. 打开开发者工具 (F12)")
    print("2. 切换到 Application/Storage → Cookies → http://localhost:3000")
    print("3. 查找 'sessionid' cookie")
    print("4. 检查它的值是否匹配上面的session key")
    print("\n如果cookie不存在或值不匹配，请:")
    print("- 退出登录")
    print("- 重新登录test1")
    print("- 然后刷新页面")


if __name__ == '__main__':
    session = find_test1_session()
    
    if session:
        test_submissions_api(session)
        show_browser_instructions(session.session_key)
    else:
        print("\n请先在浏览器中登录test1，然后重新运行此脚本")

