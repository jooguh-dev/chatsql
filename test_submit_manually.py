#!/usr/bin/env python
"""
手动测试提交功能
模拟一个真实的提交请求
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
from django.contrib.auth.models import AnonymousUser
from exercises.views import SubmitQueryView
from django.db import connection
import json


def test_submit_without_auth():
    """测试未认证用户的提交"""
    print("=" * 80)
    print("测试1: 未认证用户提交")
    print("=" * 80)
    
    factory = RequestFactory()
    request = factory.post(
        '/api/exercises/1/submit/',
        data=json.dumps({'query': 'SELECT * FROM products LIMIT 1'}),
        content_type='application/json'
    )
    request.user = AnonymousUser()
    
    view = SubmitQueryView()
    response = view.post(request, exercise_id=1)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应数据: {response.data}")
    
    # 检查数据库
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count = cursor.fetchone()[0]
        print(f"\nsubmissions表中的记录数: {count}")
    
    return response


def test_submit_with_auth():
    """测试已认证用户的提交"""
    print("\n" + "=" * 80)
    print("测试2: 已认证用户提交")
    print("=" * 80)
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # 获取或创建测试用户
    try:
        user = User.objects.get(username='test1')
    except User.DoesNotExist:
        print("❌ 用户test1不存在，请先创建用户")
        return None
    
    print(f"使用用户: {user.username} (id={user.id})")
    
    factory = RequestFactory()
    request = factory.post(
        '/api/exercises/1/submit/',
        data=json.dumps({'query': 'SELECT * FROM products LIMIT 1'}),
        content_type='application/json'
    )
    request.user = user
    
    # 检查用户是否已认证
    print(f"用户是否已认证: {request.user.is_authenticated}")
    
    view = SubmitQueryView()
    response = view.post(request, exercise_id=1)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应数据: {response.data}")
    
    # 检查数据库
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count_before = cursor.fetchone()[0]
        
        # 等待一下（如果有异步操作）
        import time
        time.sleep(0.5)
        
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count_after = cursor.fetchone()[0]
        
        print(f"\n提交前submissions表中的记录数: {count_before}")
        print(f"提交后submissions表中的记录数: {count_after}")
        
        if count_after > count_before:
            print("✅ 数据已成功保存!")
            # 显示最新的一条记录
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
    
    return response


def check_gcp_users_table():
    """检查GCP users表中的用户"""
    print("\n" + "=" * 80)
    print("检查GCP users表")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT id, username FROM users')
        users = cursor.fetchall()
        
        if users:
            print(f"GCP users表中的用户:")
            for user in users:
                print(f"  id={user[0]}, username={user[1]}")
        else:
            print("❌ GCP users表中没有用户")
    
    # 检查Django User表
    print("\n检查Django User表:")
    from django.contrib.auth import get_user_model
    User = get_user_model()
    django_users = User.objects.all()
    if django_users:
        for user in django_users:
            print(f"  id={user.id}, username={user.username}, is_authenticated={user.is_authenticated}")
    else:
        print("  Django User表中没有用户")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("手动测试提交功能")
    print("=" * 80)
    
    # 检查用户
    check_gcp_users_table()
    
    # 测试未认证
    test_submit_without_auth()
    
    # 测试已认证
    test_submit_with_auth()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

