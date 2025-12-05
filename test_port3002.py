#!/usr/bin/env python
"""
测试port 3002的配置
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

from django.conf import settings

print("=" * 80)
print("检查Port 3002的配置")
print("=" * 80)

print("\n1. CORS配置:")
print(f"   CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")
print(f"   CORS_ALLOW_CREDENTIALS: {settings.CORS_ALLOW_CREDENTIALS}")

print("\n2. Session Cookie配置:")
print(f"   SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")
print(f"   SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
print(f"   SESSION_COOKIE_HTTPONLY: {getattr(settings, 'SESSION_COOKIE_HTTPONLY', 'Not set')}")
print(f"   SESSION_COOKIE_AGE: {getattr(settings, 'SESSION_COOKIE_AGE', 'Not set')}")

print("\n3. CSRF配置:")
print(f"   CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")

# 检查3002端口是否在配置中
has_3002 = any('3002' in origin for origin in settings.CORS_ALLOWED_ORIGINS)
print(f"\n✅ Port 3002在CORS配置中: {has_3002}")

if not has_3002:
    print("❌ Port 3002不在CORS配置中，需要添加！")

print("\n" + "=" * 80)

