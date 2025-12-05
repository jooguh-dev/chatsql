#!/usr/bin/env python
"""
实时检查submissions表，帮助调试
"""

import os
import sys
import django
from pathlib import Path
import time

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


def monitor_submissions(interval=2, duration=60):
    """
    监控submissions表的变化
    
    Args:
        interval: 检查间隔（秒）
        duration: 监控时长（秒）
    """
    print("=" * 80)
    print("开始监控submissions表")
    print("=" * 80)
    print(f"检查间隔: {interval}秒")
    print(f"监控时长: {duration}秒")
    print("请在浏览器中提交一个查询，然后观察这里的变化...")
    print("按 Ctrl+C 停止监控")
    print("=" * 80)
    print()
    
    start_time = time.time()
    last_count = None
    
    try:
        while time.time() - start_time < duration:
            with connection.cursor() as cursor:
                cursor.execute('USE chatsql_system')
                cursor.execute('SELECT COUNT(*) FROM submissions')
                current_count = cursor.fetchone()[0]
                
                if last_count is not None and current_count != last_count:
                    print(f"\n🔄 检测到变化!")
                    print(f"   之前: {last_count} 条")
                    print(f"   现在: {current_count} 条")
                    print(f"   新增: {current_count - last_count} 条")
                    
                    # 显示最新记录
                    cursor.execute("""
                        SELECT id, query, status, exercise_id, user_id, created_at
                        FROM submissions
                        ORDER BY created_at DESC
                        LIMIT 1
                    """)
                    latest = cursor.fetchone()
                    if latest:
                        print(f"\n   最新记录:")
                        print(f"     ID: {latest[0]}")
                        print(f"     查询: {latest[1][:60]}...")
                        print(f"     状态: {latest[2]}")
                        print(f"     exercise_id: {latest[3]}")
                        print(f"     user_id: {latest[4]}")
                        print(f"     时间: {latest[5]}")
                    print()
                elif last_count is None:
                    print(f"当前记录数: {current_count}")
                
                last_count = current_count
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n监控已停止")
    
    print("\n" + "=" * 80)
    print("最终状态:")
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute('SELECT COUNT(*) FROM submissions')
        final_count = cursor.fetchone()[0]
        print(f"submissions表记录数: {final_count}")
        
        if final_count > 0:
            cursor.execute("""
                SELECT id, query, status, exercise_id, user_id, created_at
                FROM submissions
                ORDER BY created_at DESC
                LIMIT 5
            """)
            print("\n最近5条记录:")
            for row in cursor.fetchall():
                print(f"  ID={row[0]}, status={row[2]}, exercise_id={row[3]}, user_id={row[4]}, time={row[5]}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='监控submissions表变化')
    parser.add_argument('--interval', type=int, default=2, help='检查间隔（秒）')
    parser.add_argument('--duration', type=int, default=60, help='监控时长（秒）')
    
    args = parser.parse_args()
    
    monitor_submissions(interval=args.interval, duration=args.duration)

