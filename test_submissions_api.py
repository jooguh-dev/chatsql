#!/usr/bin/env python
"""
测试submissions API端点
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
from django.contrib.sessions.middleware import SessionMiddleware
from exercises.views import SubmissionListView
from django.db import connection


def test_submissions_api():
    """测试submissions API"""
    print("=" * 80)
    print("测试Submissions API")
    print("=" * 80)
    
    # 1. 检查数据库中的数据
    print("\n1. 检查数据库中的submissions:")
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute("""
            SELECT id, user_id, exercise_id, status, created_at
            FROM submissions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if rows:
            print(f"   找到 {len(rows)} 条记录:")
            for row in rows:
                print(f"     ID={row[0]}, user_id={row[1]}, exercise_id={row[2]}, status={row[3]}")
        else:
            print("   ❌ 没有找到任何记录")
            return
    
    # 2. 测试API（使用不同的user_id）
    print("\n2. 测试API端点:")
    
    # 获取数据库中的user_id和exercise_id
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT DISTINCT user_id FROM submissions LIMIT 1')
        db_user_id = cursor.fetchone()[0]
        cursor.execute('SELECT DISTINCT exercise_id FROM submissions LIMIT 1')
        db_exercise_id = cursor.fetchone()[0]
    
    print(f"   使用数据库中的 user_id={db_user_id}, exercise_id={db_exercise_id}")
    
    factory = RequestFactory()
    request = factory.get(f'/api/exercises/{db_exercise_id}/submissions/')
    
    # 创建session并设置user_id
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    request.session['user_id'] = db_user_id
    request.session['username'] = 'test_user'
    request.session.save()
    
    print(f"   Session user_id: {request.session.get('user_id')}")
    print(f"   Session keys: {list(request.session.keys())}")
    
    # 调用API
    view = SubmissionListView()
    try:
        response = view.get(request, exercise_id=db_exercise_id)
        print(f"\n   响应状态码: {response.status_code}")
        print(f"   响应数据: {response.data}")
        
        if response.status_code == 200:
            submissions = response.data
            print(f"   ✅ 成功获取 {len(submissions)} 条提交记录")
            if submissions:
                print(f"   第一条记录: id={submissions[0]['id']}, status={submissions[0]['status']}")
        else:
            print(f"   ❌ API返回错误: {response.data}")
    except Exception as e:
        print(f"   ❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 测试不同的user_id（应该返回空）
    print("\n3. 测试不同的user_id（应该返回空）:")
    request.session['user_id'] = 999  # 不存在的user_id
    request.session.save()
    
    try:
        response = view.get(request, exercise_id=db_exercise_id)
        print(f"   响应状态码: {response.status_code}")
        print(f"   响应数据长度: {len(response.data) if response.status_code == 200 else 0}")
        if response.status_code == 200 and len(response.data) == 0:
            print("   ✅ 正确返回空数组（user_id不匹配）")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")


if __name__ == '__main__':
    test_submissions_api()

