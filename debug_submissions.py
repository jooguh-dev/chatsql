#!/usr/bin/env python
"""
调试脚本：逐步排查为什么submissions表没有数据
"""

import os
import sys
import django
from pathlib import Path

# 设置Django环境
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
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_step_1_database_connection():
    """步骤1: 检查数据库连接"""
    print("\n" + "="*80)
    print("步骤1: 检查数据库连接")
    print("="*80)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT DATABASE()')
            current_db = cursor.fetchone()[0]
            print(f"✅ 当前数据库: {current_db}")
            
            # 检查是否能切换到chatsql_system
            cursor.execute('USE chatsql_system')
            cursor.execute('SELECT DATABASE()')
            current_db = cursor.fetchone()[0]
            print(f"✅ 成功切换到: {current_db}")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def check_step_2_table_exists():
    """步骤2: 检查表是否存在"""
    print("\n" + "="*80)
    print("步骤2: 检查submissions表是否存在")
    print("="*80)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('USE chatsql_system')
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'chatsql_system' 
                AND table_name = 'submissions'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print("✅ submissions表存在")
                
                # 检查表结构
                cursor.execute("""
                    DESCRIBE submissions
                """)
                columns = cursor.fetchall()
                print("\n表结构:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                
                return True
            else:
                print("❌ submissions表不存在!")
                return False
    except Exception as e:
        print(f"❌ 检查表失败: {e}")
        return False


def check_step_3_problems_table():
    """步骤3: 检查problems表和数据"""
    print("\n" + "="*80)
    print("步骤3: 检查problems表和数据")
    print("="*80)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('USE chatsql_system')
            
            # 检查problems表
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'chatsql_system' 
                AND table_name = 'problems'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                print("❌ problems表不存在!")
                return False
            
            print("✅ problems表存在")
            
            # 获取problems数据
            cursor.execute('SELECT id, title FROM problems LIMIT 5')
            problems = cursor.fetchall()
            
            if problems:
                print(f"\n✅ problems表中有 {len(problems)} 条记录（显示前5条）:")
                for prob in problems:
                    print(f"  - id={prob[0]}, title={prob[1]}")
                return True
            else:
                print("⚠️  problems表中没有数据")
                return False
    except Exception as e:
        print(f"❌ 检查problems表失败: {e}")
        return False


def check_step_4_users_table():
    """步骤4: 检查users表和数据"""
    print("\n" + "="*80)
    print("步骤4: 检查users表和数据")
    print("="*80)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('USE chatsql_system')
            
            # 检查users表
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'chatsql_system' 
                AND table_name = 'users'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                print("❌ users表不存在!")
                return False
            
            print("✅ users表存在")
            
            # 获取users数据
            cursor.execute('SELECT id, username FROM users LIMIT 5')
            users = cursor.fetchall()
            
            if users:
                print(f"\n✅ users表中有 {len(users)} 条记录（显示前5条）:")
                for user in users:
                    print(f"  - id={user[0]}, username={user[1]}")
                return True
            else:
                print("⚠️  users表中没有数据")
                return False
    except Exception as e:
        print(f"❌ 检查users表失败: {e}")
        return False


def check_step_5_test_insert():
    """步骤5: 测试插入数据"""
    print("\n" + "="*80)
    print("步骤5: 测试插入数据到submissions表")
    print("="*80)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('USE chatsql_system')
            
            # 获取一个有效的exercise_id和user_id
            cursor.execute('SELECT id FROM problems LIMIT 1')
            problem = cursor.fetchone()
            if not problem:
                print("❌ 无法测试: problems表中没有数据")
                return False
            
            exercise_id = problem[0]
            print(f"✅ 使用exercise_id={exercise_id}")
            
            cursor.execute('SELECT id FROM users LIMIT 1')
            user = cursor.fetchone()
            if not user:
                print("❌ 无法测试: users表中没有数据")
                return False
            
            user_id = user[0]
            print(f"✅ 使用user_id={user_id}")
            
            # 尝试插入测试数据
            test_query = "SELECT 1"
            test_status = "correct"
            test_exec_time = 0.001
            
            print(f"\n尝试插入测试数据...")
            print(f"  query: {test_query}")
            print(f"  status: {test_status}")
            print(f"  execution_time: {test_exec_time}")
            print(f"  exercise_id: {exercise_id}")
            print(f"  user_id: {user_id}")
            
            cursor.execute(
                '''INSERT INTO submissions 
                   (query, status, execution_time, exercise_id, user_id, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, NOW(6), NOW(6))''',
                [test_query, test_status, test_exec_time, exercise_id, user_id]
            )
            
            connection.commit()
            
            print("✅ 测试数据插入成功!")
            
            # 验证数据是否真的插入了
            cursor.execute('SELECT COUNT(*) FROM submissions')
            count = cursor.fetchone()[0]
            print(f"✅ submissions表现在有 {count} 条记录")
            
            # 删除测试数据
            cursor.execute('DELETE FROM submissions WHERE query = %s', [test_query])
            connection.commit()
            print("✅ 测试数据已删除")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试插入失败: {e}")
        import traceback
        traceback.print_exc()
        connection.rollback()
        return False


def check_step_6_view_code():
    """步骤6: 检查views.py代码逻辑"""
    print("\n" + "="*80)
    print("步骤6: 检查代码逻辑")
    print("="*80)
    
    views_file = BASE_DIR / 'exercises' / 'views.py'
    
    if not views_file.exists():
        print("❌ views.py文件不存在!")
        return False
    
    print("✅ views.py文件存在")
    
    # 读取文件内容
    with open(views_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键函数
    checks = {
        'save_submission_to_gcp函数存在': 'def save_submission_to_gcp' in content,
        'SubmitQueryView调用save_submission_to_gcp': 'save_submission_to_gcp(' in content,
        '检查user_id是否为None': 'if user_id is None' in content,
        '检查exercise_id是否存在': 'SELECT id FROM problems WHERE id' in content,
        '执行INSERT语句': 'INSERT INTO submissions' in content,
        '提交事务': 'connection.commit()' in content,
    }
    
    print("\n代码检查:")
    all_ok = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_ok = False
    
    # 检查SubmitQueryView是否有认证要求
    if 'class SubmitQueryView' in content:
        if 'permission_classes' in content.split('class SubmitQueryView')[1].split('def post')[0]:
            print("  ✅ SubmitQueryView有认证要求")
        else:
            print("  ⚠️  SubmitQueryView没有认证要求（可能导致user_id为None）")
            all_ok = False
    
    return all_ok


def main():
    """主函数：运行所有检查步骤"""
    print("\n" + "="*80)
    print("开始调试submissions表数据问题")
    print("="*80)
    
    results = []
    
    results.append(("数据库连接", check_step_1_database_connection()))
    results.append(("submissions表存在", check_step_2_table_exists()))
    results.append(("problems表和数据", check_step_3_problems_table()))
    results.append(("users表和数据", check_step_4_users_table()))
    results.append(("测试插入数据", check_step_5_test_insert()))
    results.append(("代码逻辑检查", check_step_6_view_code()))
    
    # 总结
    print("\n" + "="*80)
    print("检查结果总结")
    print("="*80)
    
    for step_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {step_name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✅ 所有检查都通过了!")
        print("\n可能的问题:")
        print("1. 用户未认证 - 检查前端是否发送了认证信息")
        print("2. exercise_id不存在 - 检查提交的exercise_id是否在problems表中")
        print("3. 错误被静默捕获 - 检查Django日志文件")
    else:
        print("\n❌ 发现问题，请根据上面的错误信息修复")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()

