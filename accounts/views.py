from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.db import IntegrityError
from .models import UserProfile, CustomUser
import os


def get_current_user(request):
    """从 session 获取当前用户"""
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None
    return None


def check_instructor(request):
    """检查当前用户是否是 instructor"""
    user = get_current_user(request)
    if not user:
        return False
    return user.is_admin or user.role == 'instructor'


@api_view(['POST'])
def signup(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    role = request.data.get('role', 'student')

    if not username or not password:
        return Response({'error': 'Username and password required'},
                        status=status.HTTP_400_BAD_REQUEST)

    # 验证角色
    if role not in ['student', 'instructor']:
        return Response({'error': 'Invalid role. Must be "student" or "instructor"'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        # 检查用户名是否已存在
        if CustomUser.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'},
                            status=status.HTTP_400_BAD_REQUEST)

        # 检查邮箱是否已存在（如果提供了邮箱）
        if email and CustomUser.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # 数据库查询错误（可能是表不存在或连接失败）
        import traceback
        error_detail = str(e)
        error_type = type(e).__name__
        traceback_str = traceback.format_exc()
        
        print(f"Database query error ({error_type}): {error_detail}")
        print(traceback_str)
        
        if 'Table' in error_detail and "doesn't exist" in error_detail:
            error_message = 'Database table "users" not found. Please ensure the table exists in chatsql_system database.'
        elif 'Connection' in error_detail or 'connect' in error_detail.lower():
            error_message = 'Database connection failed. Please check your GCP database configuration.'
        else:
            error_message = f'Database error: {error_detail}'
        
        return Response({
            'error': error_message,
            'error_type': error_type
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        # 先设置密码哈希
        password_hash = make_password(password)
        
        # 创建用户对象（不设置 created_at，让数据库使用默认值）
        user = CustomUser(
            username=username,
            email=email or f'{username}@example.com',  # 如果没有提供邮箱，使用默认值
            password_hash=password_hash,
            is_admin=(role == 'instructor')
            # created_at 不设置，让数据库使用默认值 CURRENT_TIMESTAMP
        )
        # 保存到数据库
        user.save()

        # 将用户信息存储到 session
        request.session['user_id'] = user.id
        request.session['username'] = user.username
        request.session['role'] = user.role

        return Response({
            'message': 'User created successfully',
            'username': user.username,
            'role': user.role,
            'userId': user.id
        }, status=status.HTTP_201_CREATED)
    except IntegrityError as e:
        return Response({'error': 'User creation failed. Username or email may already exist.'},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # 捕获其他可能的错误（如数据库连接错误）
        import traceback
        error_detail = str(e)
        error_type = type(e).__name__
        traceback_str = traceback.format_exc()
        
        # 记录详细错误信息
        print(f"Signup error ({error_type}): {error_detail}")
        print(traceback_str)
        
        # 返回更友好的错误信息
        if 'Table' in error_detail and "doesn't exist" in error_detail:
            error_message = 'Database table not found. Please ensure the user table exists in the database.'
        elif 'Connection' in error_detail or 'connect' in error_detail.lower():
            error_message = 'Database connection failed. Please check your database configuration.'
        elif 'column' in error_detail.lower() or 'field' in error_detail.lower():
            error_message = f'Database field error: {error_detail}'
        else:
            error_message = f'User creation failed: {error_detail}'
        
        return Response({
            'error': error_message,
            'error_type': error_type,
            'detail': error_detail if 'DEBUG' in os.environ else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password required'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        # 从 GCP 数据库查找用户
        user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        return Response({'error': 'Invalid username or password'},
                        status=status.HTTP_401_UNAUTHORIZED)

    # 验证密码
    if not user.check_password(password):
        return Response({'error': 'Invalid username or password'},
                        status=status.HTTP_401_UNAUTHORIZED)

    # 将用户信息存储到 session
    request.session['user_id'] = user.id
    request.session['username'] = user.username
    request.session['role'] = user.role
    request.session.set_expiry(86400 * 7)  # 7天过期
    
    # 显式保存session，确保cookie被设置
    request.session.save()
    
    # 记录日志
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"=== User Login ===")
    logger.info(f"user_id={user.id}, username={user.username}")
    logger.info(f"session_key={request.session.session_key}")
    logger.info(f"session modified={request.session.modified}")
    logger.info(f"session keys={list(request.session.keys())}")

    # 创建响应
    response = Response({
        "message": "Login successful",
        "username": user.username,
        "role": user.role,
        "userId": user.id
    }, status=status.HTTP_200_OK)
    
    # 确保session cookie被设置
    # Django会自动设置cookie，但我们可以显式确保
    if request.session.session_key:
        logger.info(f"Session cookie should be set: {request.session.session_key}")
    
    return response


@api_view(['POST'])
def logout_view(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return Response(
            {"error": "User is not logged in"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 清除 session
    request.session.flush()
    
    return Response(
        {"message": "Logout successful"},
        status=status.HTTP_200_OK
    )


@api_view(['GET', 'POST'])
def debug_user_table(request):
    """调试端点：检查 user 表状态，POST 请求可以创建表"""
    try:
        from django.db import connection
        
        # 检查数据库连接
        with connection.cursor() as cursor:
            # 检查表是否存在（表名是 users）
            cursor.execute("SHOW TABLES LIKE 'users'")
            table_exists = cursor.fetchone() is not None
            
            # 如果是 POST 请求且表不存在，尝试创建表
            if request.method == 'POST' and not table_exists:
                try:
                    create_table_sql = """
                    CREATE TABLE `users` (
                        `id` INT NOT NULL AUTO_INCREMENT,
                        `username` VARCHAR(50) NOT NULL UNIQUE,
                        `email` VARCHAR(255) NOT NULL UNIQUE,
                        `password_hash` VARCHAR(255) NOT NULL,
                        `is_admin` TINYINT(1) DEFAULT 0,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (`id`),
                        INDEX `idx_username` (`username`),
                        INDEX `idx_email` (`email`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """
                    cursor.execute(create_table_sql)
                    table_exists = True
                    return Response({
                        'message': 'Table "users" created successfully',
                        'table_exists': True
                    }, status=status.HTTP_201_CREATED)
                except Exception as create_error:
                    return Response({
                        'error': f'Failed to create table: {str(create_error)}',
                        'table_exists': False
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if not table_exists:
                return Response({
                    'error': 'Table "users" does not exist',
                    'table_exists': False,
                    'hint': 'Send a POST request to this endpoint to create the table, or run the SQL script in create_user_table.sql'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 获取表结构
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            
            # 尝试查询用户数量
            try:
                user_count = CustomUser.objects.count()
            except Exception as e:
                user_count = f"Error: {str(e)}"
            
            return Response({
                'table_exists': True,
                'table_structure': [{'field': col[0], 'type': col[1], 'null': col[2], 'key': col[3], 'default': col[4]} for col in columns],
                'user_count': user_count,
                'database': connection.settings_dict['NAME']
            }, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc() if 'DEBUG' in os.environ else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def me(request):
    user_id = request.session.get('user_id')
    
    if user_id:
        try:
            user = CustomUser.objects.get(id=user_id)
            return Response({
                "authenticated": True,
                "username": user.username,
                "role": user.role,
                "userId": user.id
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            # Session 中的用户不存在，清除 session
            request.session.flush()
            return Response(
                {"authenticated": False},
                status=status.HTTP_200_OK
            )

    return Response(
        {"authenticated": False},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def profile(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        user = CustomUser.objects.get(id=user_id)
        return Response({
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_admin": user.is_admin,
            "message": "This is a protected endpoint",
        }, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        request.session.flush()
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================
# Instructor APIs
# ============================================

@api_view(['GET'])
def instructor_stats(request):
    """GET /api/instructor/stats/"""
    
    if not check_instructor(request):
        return Response({'error': 'Unauthorized'}, status=403)
    
    from exercises.models import Exercise, Submission
    
    # 统计学生数量（非管理员用户）
    total_students = CustomUser.objects.filter(is_admin=False).count()
    total_exercises = Exercise.objects.count()
    total_submissions = Submission.objects.count()
    
    if total_submissions > 0:
        correct_submissions = Submission.objects.filter(status='correct').count()
        avg_completion_rate = round((correct_submissions / total_submissions) * 100, 1)
    else:
        avg_completion_rate = 0
    
    return Response({
        'total_students': total_students,
        'total_exercises': total_exercises,
        'total_submissions': total_submissions,
        'average_completion_rate': avg_completion_rate
    })


@api_view(['GET'])
def instructor_students(request):
    """GET /api/instructor/students/"""
    
    if not check_instructor(request):
        return Response({'error': 'Unauthorized'}, status=403)
    
    from exercises.models import Submission
    
    # 获取所有非管理员用户（学生）
    students = CustomUser.objects.filter(is_admin=False).order_by('-created_at')
    
    data = []
    for student in students:
        # 统计该学生的提交数量
        submissions_count = Submission.objects.filter(user_id=student.id).count()
        data.append({
            'id': student.id,
            'username': student.username,
            'email': student.email,
            'student_id': f"STU{student.id:06d}",
            'date_joined': student.created_at,
            'submissions_count': submissions_count
        })

    print("DEBUG - First student:", data[0] if data else "No students")
    
    return Response(data)


@api_view(['GET'])
def instructor_student_detail(request, student_id):
    """GET /api/instructor/students/{id}/"""
    
    if not check_instructor(request):
        return Response({'error': 'Unauthorized'}, status=403)
    
    from exercises.models import Submission
    
    try:
        student = CustomUser.objects.get(id=student_id, is_admin=False)
    except CustomUser.DoesNotExist:
        return Response({'error': 'Student not found'}, status=404)
    
    submissions = Submission.objects.filter(user_id=student.id).select_related('exercise').order_by('-created_at')[:20]
    
    data = {
        'id': student.id,
        'username': student.username,
        'email': student.email,
        'student_id': f"STU{student.id:06d}",
        'date_joined': student.created_at,
        'submissions': [{
            'id': sub.id,
            'exercise_title': sub.exercise.title,
            'status': sub.status,
            'created_at': sub.created_at,
        } for sub in submissions]
    }
    
    return Response(data)


@api_view(['GET'])
def instructor_recent_activity(request):
    """GET /api/instructor/recent-activity/"""
    
    if not check_instructor(request):
        return Response({'error': 'Unauthorized'}, status=403)
    
    from exercises.models import Submission
    
    recent_submissions = Submission.objects.select_related('exercise').order_by('-created_at')[:20]
    
    data = []
    for sub in recent_submissions:
        # 获取用户信息
        try:
            user = CustomUser.objects.get(id=sub.user_id)
            username = user.username
        except CustomUser.DoesNotExist:
            username = f"User {sub.user_id}"
        
        data.append({
            'id': sub.id,
            'user': username,
            'action': f'Submitted answer to "{sub.exercise.title}"',
            'date': sub.created_at,
            'status': sub.status
        })
    
    return Response(data)