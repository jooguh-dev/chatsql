#!/usr/bin/env python
"""
修复submissions表的外键约束
将exercise_id从指向exercises表改为指向problems表
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


def check_foreign_keys():
    """检查当前的外键约束"""
    print("=" * 80)
    print("检查当前的外键约束")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        
        # 检查exercise_id的外键约束
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME,
                TABLE_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'chatsql_system'
            AND TABLE_NAME = 'submissions'
            AND COLUMN_NAME = 'exercise_id'
        """)
        
        results = cursor.fetchall()
        
        if results:
            print("\n找到的外键约束:")
            for row in results:
                print(f"  约束名: {row[0]}")
                print(f"  表: {row[1]}")
                print(f"  列: {row[2]}")
                print(f"  引用表: {row[3]}")
                print(f"  引用列: {row[4]}")
                print()
            return results
        else:
            print("\n未找到外键约束")
            return []


def fix_foreign_key():
    """修复外键约束"""
    print("=" * 80)
    print("修复外键约束")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        
        # 1. 查找并删除旧的外键约束（指向exercises表）
        cursor.execute("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'chatsql_system'
            AND TABLE_NAME = 'submissions'
            AND COLUMN_NAME = 'exercise_id'
            AND REFERENCED_TABLE_NAME = 'exercises'
        """)
        
        old_constraints = cursor.fetchall()
        
        if old_constraints:
            for constraint in old_constraints:
                constraint_name = constraint[0]
                print(f"\n删除旧的外键约束 (exercise_id -> exercises): {constraint_name}")
                try:
                    cursor.execute(f'ALTER TABLE submissions DROP FOREIGN KEY {constraint_name}')
                    print(f"✅ 成功删除约束: {constraint_name}")
                except Exception as e:
                    print(f"⚠️  删除约束失败（可能不存在）: {e}")
        
        # 1.5. 查找并删除旧的外键约束（user_id指向auth_user）
        cursor.execute("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'chatsql_system'
            AND TABLE_NAME = 'submissions'
            AND COLUMN_NAME = 'user_id'
            AND REFERENCED_TABLE_NAME = 'auth_user'
        """)
        
        old_user_constraints = cursor.fetchall()
        
        if old_user_constraints:
            for constraint in old_user_constraints:
                constraint_name = constraint[0]
                print(f"\n删除旧的外键约束 (user_id -> auth_user): {constraint_name}")
                try:
                    cursor.execute(f'ALTER TABLE submissions DROP FOREIGN KEY {constraint_name}')
                    print(f"✅ 成功删除约束: {constraint_name}")
                except Exception as e:
                    print(f"⚠️  删除约束失败（可能不存在）: {e}")
        
        # 2. 检查是否已经有指向problems表的外键
        cursor.execute("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'chatsql_system'
            AND TABLE_NAME = 'submissions'
            AND COLUMN_NAME = 'exercise_id'
            AND REFERENCED_TABLE_NAME = 'problems'
        """)
        
        existing = cursor.fetchall()
        
        if existing:
            print(f"\n✅ 外键约束已存在，指向problems表: {existing[0][0]}")
        else:
            # 3. 检查并修改数据类型（如果需要）
            print("\n检查数据类型...")
            cursor.execute("""
                SELECT 
                    (SELECT DATA_TYPE FROM information_schema.COLUMNS 
                     WHERE TABLE_SCHEMA = 'chatsql_system' 
                     AND TABLE_NAME = 'submissions' AND COLUMN_NAME = 'exercise_id') as sub_type,
                    (SELECT DATA_TYPE FROM information_schema.COLUMNS 
                     WHERE TABLE_SCHEMA = 'chatsql_system' 
                     AND TABLE_NAME = 'problems' AND COLUMN_NAME = 'id') as prob_type
            """)
            types = cursor.fetchone()
            sub_type = types[0]
            prob_type = types[1]
            
            print(f"  submissions.exercise_id: {sub_type}")
            print(f"  problems.id: {prob_type}")
            
            if sub_type != prob_type:
                print(f"\n修改submissions.exercise_id的类型从{sub_type}改为{prob_type}...")
                try:
                    cursor.execute(f"""
                        ALTER TABLE submissions
                        MODIFY COLUMN exercise_id {prob_type} NOT NULL
                    """)
                    print(f"✅ 成功修改列类型为{prob_type}")
                except Exception as e:
                    print(f"❌ 修改列类型失败: {e}")
                    return False
            
            # 4. 创建新的外键约束（指向problems表）
            print("\n创建新的外键约束（指向problems表）...")
            try:
                cursor.execute("""
                    ALTER TABLE submissions
                    ADD CONSTRAINT submissions_exercise_id_fk_problems
                    FOREIGN KEY (exercise_id) REFERENCES problems(id)
                """)
                print("✅ 成功创建外键约束，指向problems表")
            except Exception as e:
                print(f"❌ 创建外键约束失败: {e}")
                print("   可能的原因:")
                print("   1. 约束已存在")
                print("   2. problems表中没有对应的数据")
                print("   3. 数据类型仍不匹配")
                return False
        
        # 5. 修复user_id外键（指向users表而不是auth_user表）
        print("\n" + "-" * 80)
        print("修复user_id外键约束")
        print("-" * 80)
        
        # 检查是否已经有指向users表的外键
        cursor.execute("""
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'chatsql_system'
            AND TABLE_NAME = 'submissions'
            AND COLUMN_NAME = 'user_id'
            AND REFERENCED_TABLE_NAME = 'users'
        """)
        
        existing_user_fk = cursor.fetchall()
        
        if existing_user_fk:
            print(f"✅ user_id外键约束已存在，指向users表: {existing_user_fk[0][0]}")
        else:
            # 检查数据类型
            cursor.execute("""
                SELECT 
                    (SELECT DATA_TYPE FROM information_schema.COLUMNS 
                     WHERE TABLE_SCHEMA = 'chatsql_system' 
                     AND TABLE_NAME = 'submissions' AND COLUMN_NAME = 'user_id') as sub_type,
                    (SELECT DATA_TYPE FROM information_schema.COLUMNS 
                     WHERE TABLE_SCHEMA = 'chatsql_system' 
                     AND TABLE_NAME = 'users' AND COLUMN_NAME = 'id') as users_type
            """)
            user_types = cursor.fetchone()
            sub_user_type = user_types[0]
            users_id_type = user_types[1]
            
            print(f"  submissions.user_id: {sub_user_type}")
            print(f"  users.id: {users_id_type}")
            
            if sub_user_type != users_id_type:
                print(f"\n修改submissions.user_id的类型从{sub_user_type}改为{users_id_type}...")
                try:
                    cursor.execute(f"""
                        ALTER TABLE submissions
                        MODIFY COLUMN user_id {users_id_type} NOT NULL
                    """)
                    print(f"✅ 成功修改列类型为{users_id_type}")
                except Exception as e:
                    print(f"❌ 修改列类型失败: {e}")
                    return False
            
            # 创建新的外键约束
            print("\n创建新的外键约束（user_id指向users表）...")
            try:
                cursor.execute("""
                    ALTER TABLE submissions
                    ADD CONSTRAINT submissions_user_id_fk_users
                    FOREIGN KEY (user_id) REFERENCES users(id)
                """)
                print("✅ 成功创建外键约束，指向users表")
            except Exception as e:
                print(f"❌ 创建外键约束失败: {e}")
                return False
        
        connection.commit()
        return True


def verify_fix():
    """验证修复结果"""
    print("\n" + "=" * 80)
    print("验证修复结果")
    print("=" * 80)
    
    constraints = check_foreign_keys()
    
    if constraints:
        for constraint in constraints:
            if constraint[3] == 'problems':
                print("\n✅ 外键约束已正确指向problems表!")
                return True
            else:
                print(f"\n❌ 外键约束仍指向错误表: {constraint[3]}")
                return False
    else:
        print("\n⚠️  未找到外键约束")
        return False


def test_insert():
    """测试插入数据"""
    print("\n" + "=" * 80)
    print("测试插入数据")
    print("=" * 80)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('USE chatsql_system')
            
            # 获取有效的ID
            cursor.execute('SELECT id FROM problems LIMIT 1')
            problem = cursor.fetchone()
            if not problem:
                print("❌ problems表中没有数据")
                return False
            
            exercise_id = problem[0]
            
            cursor.execute('SELECT id FROM users LIMIT 1')
            user = cursor.fetchone()
            if not user:
                print("❌ users表中没有数据")
                return False
            
            user_id = user[0]
            
            # 尝试插入
            print(f"\n尝试插入: exercise_id={exercise_id}, user_id={user_id}")
            cursor.execute(
                '''INSERT INTO submissions 
                   (query, status, execution_time, exercise_id, user_id, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, NOW(6), NOW(6))''',
                ['SELECT 1', 'correct', 0.001, exercise_id, user_id]
            )
            
            connection.commit()
            print("✅ 插入成功!")
            
            # 删除测试数据
            cursor.execute('DELETE FROM submissions WHERE query = %s', ['SELECT 1'])
            connection.commit()
            print("✅ 测试数据已删除")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试插入失败: {e}")
        connection.rollback()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("修复submissions表的外键约束")
    print("=" * 80)
    
    # 1. 检查当前状态
    check_foreign_keys()
    
    # 2. 修复
    if fix_foreign_key():
        # 3. 验证
        if verify_fix():
            # 4. 测试
            if test_insert():
                print("\n" + "=" * 80)
                print("✅ 所有修复完成，外键约束已正确设置!")
                print("=" * 80)
            else:
                print("\n" + "=" * 80)
                print("⚠️  修复完成，但测试插入失败")
                print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("❌ 验证失败，请手动检查")
            print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ 修复失败")
        print("=" * 80)

