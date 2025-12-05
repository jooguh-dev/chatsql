#!/usr/bin/env python
"""
检查特定session key的状态
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

# 从用户提供的cookie值
session_keys = [
    'test18233qylkey3yam8y72h25a1k959',
    '24woc5rkh9bsix7t6tz33d7tr3z7mjtj'
]

print("=" * 80)
print("检查浏览器中的Session Cookie")
print("=" * 80)

for i, session_key in enumerate(session_keys, 1):
    print(f"\nCookie #{i}: {session_key}")
    print("-" * 80)
    
    try:
        session = Session.objects.get(session_key=session_key)
        
        # 检查是否过期
        is_expired = session.expire_date < timezone.now()
        print(f"过期时间: {session.expire_date}")
        print(f"是否过期: {'❌ 已过期' if is_expired else '✅ 有效'}")
        
        if not is_expired:
            # 解码session数据
            session_data = session.get_decoded()
            user_id = session_data.get('user_id')
            username = session_data.get('username')
            role = session_data.get('role')
            
            print(f"user_id: {user_id}")
            print(f"username: {username}")
            print(f"role: {role}")
            print(f"所有keys: {list(session_data.keys())}")
            
            if user_id == 1 and username == 'test1':
                print("✅ 这是test1的session!")
            else:
                print(f"⚠️  这不是test1的session (user_id={user_id}, username={username})")
        else:
            print("❌ Session已过期，需要重新登录")
            
    except Session.DoesNotExist:
        print("❌ Session不存在（可能已被删除）")
    except Exception as e:
        print(f"❌ 检查失败: {e}")

print("\n" + "=" * 80)
print("建议:")
print("1. 如果所有session都过期，请清除浏览器cookie并重新登录")
print("2. 如果session存在但user_id不是1，请使用test1重新登录")
print("3. 登录后，检查新的sessionid cookie")
print("=" * 80)

