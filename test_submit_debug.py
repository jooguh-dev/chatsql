#!/usr/bin/env python
"""
详细调试提交功能，检查为什么数据没有保存
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

from django.test import RequestFactory
from django.db import connection
from exercises.views import save_submission_to_gcp
import json
import logging

# 配置日志以查看详细信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_save_function_directly():
    """直接测试save_submission_to_gcp函数"""
    print("=" * 80)
    print("测试1: 直接调用save_submission_to_gcp函数")
    print("=" * 80)
    
    # 检查数据库中的记录数
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count_before = cursor.fetchone()[0]
        print(f"提交前记录数: {count_before}")
    
    # 直接调用函数
    try:
        save_submission_to_gcp(
            user_id=1,
            exercise_id=1,
            query="SELECT * FROM products LIMIT 1",
            status='correct',
            execution_time=0.123
        )
        print("✅ 函数调用完成（无异常）")
    except Exception as e:
        print(f"❌ 函数调用失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 再次检查记录数
    import time
    time.sleep(0.5)  # 等待一下
    
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count_after = cursor.fetchone()[0]
        print(f"提交后记录数: {count_after}")
        
        if count_after > count_before:
            print("✅ 数据已成功保存!")
            # 显示最新记录
            cursor.execute("""
                SELECT id, query, status, exercise_id, user_id, created_at
                FROM submissions
                ORDER BY created_at DESC
                LIMIT 1
            """)
            latest = cursor.fetchone()
            if latest:
                print(f"\n最新记录:")
                print(f"  ID: {latest[0]}")
                print(f"  查询: {latest[1][:50]}...")
                print(f"  状态: {latest[2]}")
                print(f"  exercise_id: {latest[3]}")
                print(f"  user_id: {latest[4]}")
                print(f"  创建时间: {latest[5]}")
        else:
            print("❌ 数据没有保存!")


def check_session_simulation():
    """模拟一个真实的请求，检查session"""
    print("\n" + "=" * 80)
    print("测试2: 模拟真实请求（带session）")
    print("=" * 80)
    
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.sessions.backends.db import SessionStore
    
    factory = RequestFactory()
    request = factory.post(
        '/api/exercises/1/submit/',
        data=json.dumps({'query': 'SELECT * FROM products LIMIT 1'}),
        content_type='application/json'
    )
    
    # 创建session并设置user_id
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # 设置user_id到session
    request.session['user_id'] = 1
    request.session['username'] = 'test1'
    request.session.save()
    
    print(f"Session key: {request.session.session_key}")
    print(f"Session user_id: {request.session.get('user_id')}")
    print(f"Session keys: {list(request.session.keys())}")
    
    # 检查提交前的记录数
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count_before = cursor.fetchone()[0]
        print(f"\n提交前记录数: {count_before}")
    
    # 调用SubmitQueryView
    from exercises.views import SubmitQueryView
    view = SubmitQueryView()
    
    try:
        response = view.post(request, exercise_id=1)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应数据: {response.data}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 等待一下
    import time
    time.sleep(1)
    
    # 检查提交后的记录数
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count_after = cursor.fetchone()[0]
        print(f"\n提交后记录数: {count_after}")
        
        if count_after > count_before:
            print("✅ 数据已成功保存!")
        else:
            print("❌ 数据没有保存!")


def check_database_state():
    """检查数据库当前状态"""
    print("\n" + "=" * 80)
    print("检查数据库状态")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        
        # 检查submissions表
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count = cursor.fetchone()[0]
        print(f"submissions表当前记录数: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT id, query, status, exercise_id, user_id, created_at
                FROM submissions
                ORDER BY created_at DESC
                LIMIT 5
            """)
            print("\n最近5条记录:")
            for row in cursor.fetchall():
                print(f"  ID={row[0]}, status={row[2]}, exercise_id={row[3]}, user_id={row[4]}, time={row[5]}")
        
        # 检查problems表
        cursor.execute('SELECT id FROM problems LIMIT 1')
        problem = cursor.fetchone()
        if problem:
            print(f"\n✅ problems表有数据，可以使用exercise_id={problem[0]}")
        else:
            print("\n❌ problems表没有数据!")
        
        # 检查users表
        cursor.execute('SELECT id FROM users LIMIT 1')
        user = cursor.fetchone()
        if user:
            print(f"✅ users表有数据，可以使用user_id={user[0]}")
        else:
            print("❌ users表没有数据!")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("详细调试提交功能")
    print("=" * 80)
    
    # 检查数据库状态
    check_database_state()
    
    # 测试1: 直接调用函数
    test_save_function_directly()
    
    # 测试2: 模拟真实请求
    check_session_simulation()
    
    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)

