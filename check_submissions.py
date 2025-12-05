#!/usr/bin/env python
"""
脚本用于检查GCP chatsql_system数据库中的submissions表数据
验证提交记录是否正确同步

使用方法:
    python check_submissions.py [--limit N]
    
或者使用Django管理命令:
    python manage.py shell < check_submissions.py
"""

import os
import sys
import django
from pathlib import Path

# 设置Django环境
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatsql.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Django设置失败: {e}")
    print("\n请确保:")
    print("1. 已激活虚拟环境 (source venv/bin/activate)")
    print("2. 已安装所有依赖 (pip install -r requirements.txt)")
    print("3. 已设置环境变量 (.env文件)")
    sys.exit(1)

from django.db import connection
from datetime import datetime


def check_submissions(limit=10):
    """
    检查submissions表中的数据
    
    Args:
        limit: 显示最近N条记录
    """
    print("=" * 80)
    print("检查GCP chatsql_system数据库中的submissions表")
    print("=" * 80)
    print()
    
    try:
        with connection.cursor() as cursor:
            # 切换到chatsql_system数据库
            cursor.execute('USE chatsql_system')
            
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = 'chatsql_system' 
                AND table_name = 'submissions'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                print("❌ 错误: submissions表不存在!")
                return
            
            print("✅ submissions表存在")
            print()
            
            # 获取总记录数
            cursor.execute('SELECT COUNT(*) FROM submissions')
            total_count = cursor.fetchone()[0]
            print(f"📊 总记录数: {total_count}")
            print()
            
            if total_count == 0:
                print("⚠️  警告: submissions表中没有数据")
                return
            
            # 获取最近的记录
            cursor.execute("""
                SELECT 
                    id,
                    query,
                    status,
                    execution_time,
                    exercise_id,
                    user_id,
                    created_at,
                    updated_at
                FROM submissions
                ORDER BY created_at DESC
                LIMIT %s
            """, [limit])
            
            rows = cursor.fetchall()
            
            print(f"📋 最近 {len(rows)} 条记录:")
            print("-" * 80)
            
            for i, row in enumerate(rows, 1):
                print(f"\n记录 #{i}:")
                print(f"  ID: {row[0]}")
                print(f"  查询 (query): {row[1][:100]}{'...' if len(row[1]) > 100 else ''}")
                print(f"  状态 (status): {row[2]}")
                print(f"  执行时间 (execution_time): {row[3] if row[3] is not None else 'NULL'}")
                print(f"  练习ID (exercise_id): {row[4]}")
                print(f"  用户ID (user_id): {row[5]}")
                print(f"  创建时间 (created_at): {row[6]}")
                print(f"  更新时间 (updated_at): {row[7]}")
                
                # 验证exercise_id是否存在于problems表
                cursor.execute('SELECT id FROM problems WHERE id = %s', [row[4]])
                problem_exists = cursor.fetchone()
                if problem_exists:
                    print(f"  ✅ exercise_id={row[4]} 存在于problems表")
                else:
                    print(f"  ❌ exercise_id={row[4]} 不存在于problems表!")
                
                # 验证user_id是否存在于users表
                cursor.execute('SELECT id FROM users WHERE id = %s', [row[5]])
                user_exists = cursor.fetchone()
                if user_exists:
                    print(f"  ✅ user_id={row[5]} 存在于users表")
                else:
                    print(f"  ❌ user_id={row[5]} 不存在于users表!")
            
            print()
            print("-" * 80)
            
            # 统计信息
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM submissions
                GROUP BY status
            """)
            status_stats = cursor.fetchall()
            
            print("\n📈 状态统计:")
            for status, count in status_stats:
                print(f"  {status}: {count} 条")
            
            print()
            
            # 按exercise_id统计
            cursor.execute("""
                SELECT 
                    exercise_id,
                    COUNT(*) as count
                FROM submissions
                GROUP BY exercise_id
                ORDER BY count DESC
                LIMIT 10
            """)
            exercise_stats = cursor.fetchall()
            
            print("📈 按练习ID统计 (前10):")
            for exercise_id, count in exercise_stats:
                print(f"  exercise_id={exercise_id}: {count} 条提交")
            
            print()
            
            # 按user_id统计
            cursor.execute("""
                SELECT 
                    user_id,
                    COUNT(*) as count
                FROM submissions
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            """)
            user_stats = cursor.fetchall()
            
            print("📈 按用户ID统计 (前10):")
            for user_id, count in user_stats:
                print(f"  user_id={user_id}: {count} 条提交")
            
            print()
            print("=" * 80)
            print("✅ 检查完成!")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='检查GCP submissions表数据')
    parser.add_argument('--limit', type=int, default=10, help='显示最近N条记录 (默认: 10)')
    
    args = parser.parse_args()
    
    check_submissions(limit=args.limit)

