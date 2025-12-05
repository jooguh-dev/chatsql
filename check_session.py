#!/usr/bin/env python
"""
检查session状态和submissions API
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

from django.db import connection
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta


def check_sessions():
    """检查所有活跃的session"""
    print("=" * 80)
    print("检查Django Sessions")
    print("=" * 80)
    
    # 获取最近24小时内的session
    recent_sessions = Session.objects.filter(
        expire_date__gt=timezone.now()
    ).order_by('-expire_date')[:10]
    
    print(f"\n找到 {recent_sessions.count()} 个活跃的session（显示最近10个）:\n")
    
    for i, session in enumerate(recent_sessions, 1):
        try:
            session_data = session.get_decoded()
            user_id = session_data.get('user_id')
            username = session_data.get('username')
            role = session_data.get('role')
            
            print(f"Session #{i}:")
            print(f"  Session Key: {session.session_key[:20]}...")
            print(f"  Expire Date: {session.expire_date}")
            print(f"  user_id: {user_id}")
            print(f"  username: {username}")
            print(f"  role: {role}")
            print(f"  All keys: {list(session_data.keys())}")
            print()
        except Exception as e:
            print(f"  Error decoding session: {e}")
            print()


def check_submissions_by_user():
    """检查submissions表中的用户ID分布"""
    print("=" * 80)
    print("检查Submissions表中的用户ID")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        
        # 获取所有不同的user_id
        cursor.execute("""
            SELECT user_id, COUNT(*) as count
            FROM submissions
            GROUP BY user_id
            ORDER BY count DESC
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"\n找到 {len(rows)} 个不同的用户ID:\n")
            for user_id, count in rows:
                print(f"  user_id={user_id}: {count} 条提交")
        else:
            print("\n❌ submissions表中没有数据")


def check_session_vs_submissions():
    """对比session中的user_id和submissions表中的user_id"""
    print("\n" + "=" * 80)
    print("对比Session和Submissions")
    print("=" * 80)
    
    # 获取所有活跃session中的user_id
    session_user_ids = set()
    recent_sessions = Session.objects.filter(
        expire_date__gt=timezone.now()
    )
    
    for session in recent_sessions:
        try:
            session_data = session.get_decoded()
            user_id = session_data.get('user_id')
            if user_id:
                session_user_ids.add(user_id)
        except:
            pass
    
    print(f"\nSession中的user_id: {sorted(session_user_ids)}")
    
    # 获取submissions表中的user_id
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute("""
            SELECT DISTINCT user_id
            FROM submissions
        """)
        submission_user_ids = {row[0] for row in cursor.fetchall()}
    
    print(f"Submissions表中的user_id: {sorted(submission_user_ids)}")
    
    # 对比
    if session_user_ids:
        print(f"\n✅ 有 {len(session_user_ids)} 个用户已登录")
        if submission_user_ids:
            matching = session_user_ids & submission_user_ids
            if matching:
                print(f"✅ 有 {len(matching)} 个用户有提交记录: {sorted(matching)}")
            else:
                print(f"⚠️  登录用户的user_id和submissions表中的user_id不匹配")
                print(f"   这可能是问题所在！")
        else:
            print("⚠️  submissions表中没有数据")
    else:
        print("\n❌ 没有活跃的session（没有用户登录）")
        print("   这就是为什么API返回401的原因！")


def test_submissions_api_with_session():
    """使用真实的session测试submissions API"""
    print("\n" + "=" * 80)
    print("测试Submissions API（使用真实session）")
    print("=" * 80)
    
    from django.test import RequestFactory
    from exercises.views import SubmissionListView
    
    # 获取一个活跃的session
    recent_sessions = Session.objects.filter(
        expire_date__gt=timezone.now()
    ).order_by('-expire_date')[:1]
    
    if not recent_sessions.exists():
        print("❌ 没有活跃的session，无法测试")
        return
    
    session = recent_sessions.first()
    session_data = session.get_decoded()
    user_id = session_data.get('user_id')
    
    if not user_id:
        print("❌ Session中没有user_id")
        return
    
    print(f"使用session: {session.session_key[:20]}...")
    print(f"user_id: {user_id}")
    
    # 获取该用户的exercise_id
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute("""
            SELECT DISTINCT exercise_id
            FROM submissions
            WHERE user_id = %s
            LIMIT 1
        """, [user_id])
        result = cursor.fetchone()
        
        if not result:
            print("❌ 该用户没有提交记录")
            return
        
        exercise_id = result[0]
        print(f"exercise_id: {exercise_id}")
    
    # 创建请求
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
                print(f"   第一条: id={submissions[0]['id']}, status={submissions[0]['status']}")
        else:
            print(f"❌ API返回错误: {response.data}")
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("检查Session和Submissions状态")
    print("=" * 80)
    
    check_sessions()
    check_submissions_by_user()
    check_session_vs_submissions()
    test_submissions_api_with_session()
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)
    print("\n提示:")
    print("1. 如果'没有活跃的session'，说明用户未登录")
    print("2. 如果session中的user_id和submissions表中的user_id不匹配，说明登录用户和提交用户不是同一个人")
    print("3. 确保在浏览器中已登录，然后刷新页面再检查")

