from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import models as dj_models
from django.utils import timezone
from .models import DatabaseSchema, Exercise, UserProgress, Submission, Problem
from .services.executor import SQLExecutor
import uuid
import json
from django.db import connection


def check_instructor(user):
    """检查用户是否是 instructor"""
    if not user.is_authenticated:
        return False
    return hasattr(user, 'profile') and user.profile.role == 'instructor'


def get_problem_from_gcp(problem_id=None):
    """
    从GCP的problems表读取数据
    如果problem_id为None，返回所有problems
    """
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        
        if problem_id:
            cursor.execute(
                'SELECT id, title, difficulty, tag, description, database_name, expected_query, expected_result, created_at '
                'FROM problems WHERE id = %s',
                [problem_id]
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'id': row[0],
                'title': row[1],
                'difficulty': row[2].lower() if row[2] else 'easy',  # Convert Easy -> easy
                'tag': row[3] or '',
                'description': row[4] or '',
                'database_name': row[5] or '',
                'expected_query': row[6] or '',
                'expected_result': row[7],
                'created_at': row[8]
            }
        else:
            cursor.execute(
                'SELECT id, title, difficulty, tag, description, database_name, expected_query, expected_result, created_at '
                'FROM problems ORDER BY id'
            )
            problems = []
            for row in cursor.fetchall():
                problems.append({
                    'id': row[0],
                    'title': row[1],
                    'difficulty': row[2].lower() if row[2] else 'easy',
                    'tag': row[3] or '',
                    'description': row[4] or '',
                    'database_name': row[5] or '',
                    'expected_query': row[6] or '',
                    'expected_result': row[7],
                    'created_at': row[8]
                })
            return problems


def get_problem_tables(problem_id):
    """从problem_tables表获取表定义信息"""
    with connection.cursor() as cursor:
        cursor.execute('USE chatsql_system')
        cursor.execute(
            'SELECT table_name, table_schema, sample_data, display_order '
            'FROM problem_tables WHERE problem_id = %s ORDER BY display_order',
            [problem_id]
        )
        tables = []
        for row in cursor.fetchall():
            tables.append({
                'table_name': row[0],
                'table_schema': row[1],
                'sample_data': row[2],
                'display_order': row[3]
            })
        return tables


def save_submission_to_gcp(user_id, exercise_id, query, status, execution_time):
    """
    保存提交记录到GCP的chatsql_system数据库的submissions表
    
    Args:
        user_id: 用户ID（int），如果为None则不保存
        exercise_id: 练习ID（bigint），必须对应problems表的id字段（外键）
        query: SQL查询语句（longtext）
        status: 状态（varchar(20)），'correct' 或 'incorrect'
        execution_time: 执行时间（double），可以为None
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"save_submission_to_gcp called with:")
    logger.info(f"  user_id={user_id} (type: {type(user_id)})")
    logger.info(f"  exercise_id={exercise_id} (type: {type(exercise_id)})")
    logger.info(f"  status={status}")
    logger.info(f"  execution_time={execution_time}")
    logger.info(f"  query length={len(query) if query else 0}")
    
    if user_id is None:
        # 如果用户未认证，不保存提交记录
        logger.warning("❌ Cannot save submission: user_id is None (user not authenticated)")
        logger.warning("   This is the most common reason for missing submissions!")
        return
    
    # 验证数据类型和值
    try:
        user_id = int(user_id)
        exercise_id = int(exercise_id)
        if execution_time is not None:
            execution_time = float(execution_time)
        # 确保status不超过20字符
        status = str(status)[:20]
        query = str(query)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid data types for submission: user_id={user_id}, exercise_id={exercise_id}, execution_time={execution_time}, error={e}")
        return
    
    try:
        with connection.cursor() as cursor:
            # 切换到chatsql_system数据库
            cursor.execute('USE chatsql_system')
            
            # 验证exercise_id是否存在于problems表中
            cursor.execute('SELECT id FROM problems WHERE id = %s', [exercise_id])
            problem_exists = cursor.fetchone()
            if not problem_exists:
                logger.error(f"Cannot save submission: exercise_id={exercise_id} does not exist in problems table")
                return
            
            # 插入数据到submissions表
            # exercise_id是外键，指向problems表的id字段
            cursor.execute(
                '''INSERT INTO submissions 
                   (query, status, execution_time, exercise_id, user_id, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, NOW(6), NOW(6))''',
                [query, status, execution_time, exercise_id, user_id]
            )
            
            # 显式提交事务
            connection.commit()
            
            # 验证数据是否真的保存了
            cursor.execute('SELECT COUNT(*) FROM submissions WHERE user_id = %s AND exercise_id = %s', [user_id, exercise_id])
            saved_count = cursor.fetchone()[0]
            
            logger.info(f"Successfully saved submission: user_id={user_id}, exercise_id={exercise_id} (points to problems.id), status={status}")
            logger.info(f"Verification: Found {saved_count} submissions for this user and exercise")
            
            # 如果保存失败，记录警告
            if saved_count == 0:
                logger.error(f"⚠️  WARNING: Data was committed but not found in database! This might indicate a transaction issue.")
            
    except Exception as e:
        # 回滚事务
        connection.rollback()
        logger.error(f"Failed to save submission to GCP: user_id={user_id}, exercise_id={exercise_id}, error={str(e)}", exc_info=True)
        raise


class SchemaListView(APIView):
    """GET /api/schemas/ - List all database schemas"""
    
    def get(self, request):
        schemas = DatabaseSchema.objects.all()
        data = [{
            'id': s.id,
            'name': s.name,
            'display_name': s.display_name,
            'description': s.description,
            'exercise_count': s.exercises.count()
        } for s in schemas]
        return Response(data)


class ExerciseListView(APIView):
    """GET /api/exercises/?schema_id=1&difficulty=easy&tag=SELECT"""
    
    def get(self, request):
        # 从GCP的problems表读取数据
        problems = get_problem_from_gcp()
        
        if not problems:
            return Response([])
        
        # Filter by difficulty
        difficulty = request.query_params.get('difficulty')
        if difficulty:
            problems = [p for p in problems if p['difficulty'].lower() == difficulty.lower()]
        
        # Filter by tag (GCP中tag是单个字符串，不是数组)
        tag = request.query_params.get('tag')
        if tag:
            problems = [p for p in problems if tag.lower() in (p.get('tag', '') or '').lower()]
        
        # 构建返回数据
        data = []
        for problem in problems:
            # 从problem_tables获取schema信息
            tables = get_problem_tables(problem['id'])
            table_name = tables[0]['table_name'] if tables else 'Unknown'
            
            # 构建schema信息
            tag_display = problem.get('tag', '').strip() if problem.get('tag') else 'Database'
            schema = {
                'id': problem['id'],
                'name': problem['database_name'].replace('chatsql_problem_', 'problem_'),
                'display_name': f"Problem {problem['id']} {tag_display}",
                'db_name': problem['database_name']
            }
            
            # 将tag字符串转换为数组
            tags = [problem['tag']] if problem.get('tag') else []
            
            data.append({
                'id': problem['id'],
                'title': problem['title'],
                'description': problem['description'],
                'difficulty': problem['difficulty'],
                'schema': schema,
                'tags': tags,
                'completed': False  # TODO: Check user progress
            })
        
        return Response(data)


class ExerciseDetailView(APIView):
    """GET /api/exercises/{id}/ - Get exercise details"""
    
    def get(self, request, exercise_id):
        # 从GCP的problems表读取数据
        problem = get_problem_from_gcp(problem_id=exercise_id)
        
        if not problem:
            return Response(
                {'error': 'Problem not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 调试日志：打印从GCP读取的数据
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Exercise detail requested for ID {exercise_id}")
        logger.info(f"Problem data from GCP: title={problem.get('title')}, description={problem.get('description')[:50] if problem.get('description') else 'None'}...")
        
        # 获取表定义信息
        tables = get_problem_tables(exercise_id)
        table_name = tables[0]['table_name'] if tables else 'Unknown'
        
        # 构建schema信息
        tag_display = problem.get('tag', '').strip() if problem.get('tag') else 'Database'
        schema = {
            'id': problem['id'],
            'name': problem['database_name'].replace('chatsql_problem_', 'problem_'),
            'display_name': f"Problem {problem['id']} {tag_display}",
            'db_name': problem['database_name']
        }
        
        # 构建初始查询（从表名生成）
        initial_query = f"SELECT \n  -- Write your query here\nFROM {table_name}"
        
        # 将tag字符串转换为数组
        tags = [problem['tag']] if problem.get('tag') else []
        
        data = {
            'id': problem['id'],
            'title': problem['title'],
            'description': problem['description'] or '',  # 确保description不为None
            'difficulty': problem['difficulty'],
            'initial_query': initial_query,
            'expected_query': problem.get('expected_query', ''),  # 添加 expected_query (solution)
            'hints': [],  # GCP中没有hints字段，返回空数组
            'schema': schema,
            'tags': tags
        }
        
        logger.info(f"Returning exercise data: title={data['title']}, description length={len(data['description'])}")
        
        return Response(data)


class ExecuteQueryView(APIView):
    """POST /api/exercises/{id}/execute/ - Execute user query"""
    
    def post(self, request, exercise_id):
        # 从GCP的problems表读取数据
        problem = get_problem_from_gcp(problem_id=exercise_id)
        
        if not problem:
            return Response(
                {'error': 'Problem not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        query = request.data.get('query', '').strip()
        
        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute query using SQLExecutor with database_name from problems table
        try:
            executor = SQLExecutor(problem['database_name'])
            result = executor.execute(query)
        except ValueError:
            # Fallback: execute against default DB (SQLite) using Django connection
            start = timezone.now()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchmany(SQLExecutor.MAX_ROWS)
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    row_list = [list(row) for row in rows]
                exec_time = (timezone.now() - start).total_seconds()
                result = {
                    'success': True,
                    'columns': columns,
                    'rows': row_list,
                    'row_count': len(row_list),
                    'execution_time': round(exec_time, 3),
                    'error': None
                }
            except Exception as e:
                exec_time = (timezone.now() - start).total_seconds()
                result = {
                    'success': False,
                    'error': str(e),
                    'columns': [],
                    'rows': [],
                    'row_count': 0,
                    'execution_time': round(exec_time, 3)
                }
        
        # Track attempt (get or create session)
        # Note: UserProgress tracking may need to be adapted for GCP problems table
        # For now, we'll skip it since it references Exercise model
        # session_id = request.session.session_key
        # if not session_id:
        #     request.session.create()
        #     session_id = request.session.session_key
        
        return Response(result)


class SubmitQueryView(APIView):
    """POST /api/exercises/{id}/submit/ - Submit and validate query"""
    
    def post(self, request, exercise_id):
        # 从GCP的problems表读取数据
        problem = get_problem_from_gcp(problem_id=exercise_id)
        
        if not problem:
            return Response(
                {'error': 'Problem not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        query = request.data.get('query', '').strip()
        
        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute both user query and expected query
        executor = None
        try:
            executor = SQLExecutor(problem['database_name'])
            user_result = executor.execute(query)
            expected_result = executor.execute(problem['expected_query'])
        except ValueError:
            # Fallback execution on default DB
            def run_on_default(q):
                start = timezone.now()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(q)
                        rows = cursor.fetchmany(SQLExecutor.MAX_ROWS)
                        columns = [col[0] for col in cursor.description] if cursor.description else []
                        row_list = [list(row) for row in rows]
                    exec_time = (timezone.now() - start).total_seconds()
                    return {
                        'success': True,
                        'columns': columns,
                        'rows': row_list,
                        'row_count': len(row_list),
                        'execution_time': round(exec_time, 3),
                        'error': None
                    }
                except Exception as e:
                    exec_time = (timezone.now() - start).total_seconds()
                    return {
                        'success': False,
                        'error': str(e),
                        'columns': [],
                        'rows': [],
                        'row_count': 0,
                        'execution_time': round(exec_time, 3)
                    }

            user_result = run_on_default(query)
            expected_result = run_on_default(problem['expected_query'])
            # Create a dummy executor for comparison in fallback case
            executor = SQLExecutor(problem['database_name']) if problem['database_name'] else None
        
        # Compare results
        if executor:
            comparison = executor.compare_results(user_result, expected_result)
        else:
            # Simple comparison if executor is not available
            comparison = {
                'correct': user_result.get('success') and expected_result.get('success') and 
                          user_result.get('row_count') == expected_result.get('row_count'),
                'message': 'Results compared (fallback mode)',
                'diff': None
            }
        
        # Save submission to GCP chatsql_system database
        import logging
        logger = logging.getLogger(__name__)
        
        # 从session获取user_id（因为使用的是CustomUser，不是Django的User）
        # 认证系统将user_id存储在request.session['user_id']中
        user_id = request.session.get('user_id')
        
        # 详细记录用户认证状态
        logger.info(f"=== Submission Save Debug ===")
        logger.info(f"Session user_id: {user_id}")
        logger.info(f"Session keys: {list(request.session.keys())}")
        logger.info(f"Django user authenticated: {request.user.is_authenticated}")
        logger.info(f"Django user: {request.user}")
        
        try:
            submission_status = 'correct' if comparison['correct'] else 'incorrect'
            exec_time = user_result.get('execution_time')
            
            logger.info(f"Attempting to save submission:")
            logger.info(f"  user_id={user_id} (from session)")
            logger.info(f"  exercise_id={exercise_id}")
            logger.info(f"  status={submission_status}")
            logger.info(f"  execution_time={exec_time}")
            logger.info(f"  query length={len(query)}")
            
            if user_id is None:
                logger.warning("⚠️  WARNING: user_id is None - submission will NOT be saved!")
                logger.warning("   This means the user is not logged in (no session['user_id']).")
                logger.warning("   User needs to login first to save submissions.")
            
            save_submission_to_gcp(
                user_id=user_id,
                exercise_id=exercise_id,
                query=query,
                status=submission_status,
                execution_time=exec_time
            )
            
            logger.info(f"=== Submission Save Completed ===")
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"❌ Failed to save submission to GCP: {e}", exc_info=True)
            logger.error(f"   user_id={user_id if 'user_id' in locals() else 'unknown'}")
            logger.error(f"   exercise_id={exercise_id if 'exercise_id' in locals() else 'unknown'}")
        
        # Update progress
        # Note: UserProgress tracking may need to be adapted for GCP problems table
        # For now, we'll skip it since it references Exercise model
        # session_id = request.session.session_key or str(uuid.uuid4())
        
        return Response({
            'correct': comparison['correct'],
            'message': comparison['message'],
            'user_result': user_result,
            'diff': comparison.get('diff')
        })


class SubmissionListView(APIView):
    """GET /api/exercises/{id}/submissions/ - Get user's submission history for an exercise"""
    
    def get(self, request, exercise_id):
        import logging
        logger = logging.getLogger(__name__)
        
        # 详细记录请求信息
        logger.info(f"=== Fetching Submissions ===")
        logger.info(f"exercise_id: {exercise_id}")
        logger.info(f"request.method: {request.method}")
        logger.info(f"request.path: {request.path}")
        
        # 检查cookie
        sessionid_cookie = request.COOKIES.get('sessionid')
        logger.info(f"Cookie 'sessionid' in request: {sessionid_cookie is not None}")
        if sessionid_cookie:
            logger.info(f"Cookie 'sessionid' value: {sessionid_cookie[:20]}...")
        else:
            logger.warning("❌ No 'sessionid' cookie in request!")
            logger.warning("   This means the browser is not sending the cookie to the server")
            logger.warning("   Check:")
            logger.warning("   1. Browser cookies (Application/Storage → Cookies)")
            logger.warning("   2. Request headers in Network tab")
            logger.warning("   3. CORS and SameSite settings")
        
        # 检查所有cookies
        logger.info(f"All cookies in request: {list(request.COOKIES.keys())}")
        
        # 检查session
        logger.info(f"session.session_key: {request.session.session_key}")
        logger.info(f"session.modified: {request.session.modified}")
        logger.info(f"session keys: {list(request.session.keys())}")
        
        # 从session获取user_id
        user_id = request.session.get('user_id')
        logger.info(f"session user_id: {user_id}")
        
        if not user_id:
            logger.warning("❌ User not authenticated - no user_id in session")
            if not sessionid_cookie:
                logger.error("   ROOT CAUSE: No sessionid cookie in request!")
                logger.error("   The browser is not sending the cookie to the server.")
                logger.error("   Possible reasons:")
                logger.error("   1. Cookie SameSite policy blocking cross-origin requests")
                logger.error("   2. Cookie was not set during login")
                logger.error("   3. Browser security settings blocking the cookie")
            else:
                logger.warning("   Session cookie exists but session has no user_id")
                logger.warning("   This might mean:")
                logger.warning("   1. Session expired")
                logger.warning("   2. Session was cleared")
                logger.warning("   3. Different session than login")
            
            return Response(
                {
                    'error': 'User not authenticated', 
                    'detail': 'No user_id in session. Please login again.',
                    'debug': {
                        'has_sessionid_cookie': sessionid_cookie is not None,
                        'session_keys': list(request.session.keys()),
                        'session_key': request.session.session_key
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            with connection.cursor() as cursor:
                cursor.execute('USE chatsql_system')
                
                # 先检查是否有任何submissions（用于调试）
                cursor.execute('SELECT COUNT(*) FROM submissions')
                total_count = cursor.fetchone()[0]
                logger.info(f"Total submissions in table: {total_count}")
                
                # 检查该exercise_id的所有submissions（用于调试）
                cursor.execute('SELECT COUNT(*) FROM submissions WHERE exercise_id = %s', [exercise_id])
                exercise_count = cursor.fetchone()[0]
                logger.info(f"Submissions for exercise_id={exercise_id}: {exercise_count}")
                
                # 检查该user_id的所有submissions（用于调试）
                cursor.execute('SELECT COUNT(*) FROM submissions WHERE user_id = %s', [user_id])
                user_count = cursor.fetchone()[0]
                logger.info(f"Submissions for user_id={user_id}: {user_count}")
                
                # 获取该用户在该练习的所有提交记录
                cursor.execute("""
                    SELECT 
                        id,
                        query,
                        status,
                        execution_time,
                        created_at,
                        updated_at
                    FROM submissions
                    WHERE exercise_id = %s AND user_id = %s
                    ORDER BY created_at DESC
                """, [exercise_id, user_id])
                
                rows = cursor.fetchall()
                logger.info(f"Found {len(rows)} submissions for user_id={user_id} and exercise_id={exercise_id}")
                
                submissions = []
                for row in rows:
                    submissions.append({
                        'id': row[0],
                        'query': row[1],
                        'status': row[2],
                        'execution_time': row[3],
                        'created_at': row[4].isoformat() if row[4] else None,
                        'updated_at': row[5].isoformat() if row[5] else None,
                    })
                
                logger.info(f"Returning {len(submissions)} submissions")
                return Response(submissions)
                
        except Exception as e:
            logger.error(f"Failed to fetch submissions: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to fetch submissions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# Instructor Exercise Management APIs
# ============================================

@api_view(['GET', 'POST'])
def instructor_exercises(request):
    """
    GET /api/instructor/exercises/ - 获取所有练习（从GCP的problems表）
    POST /api/instructor/exercises/ - 创建新练习（暂不支持，problems表是只读的）
    """
    
    # 使用accounts中的check_instructor函数
    from accounts.views import check_instructor as check_instructor_accounts
    if not check_instructor_accounts(request):
        return Response({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'GET':
        # 从GCP的problems表获取所有题目
        try:
            problems = Problem.objects.all().order_by('id')
            data = [{
                'id': p.id,
                'title': p.title,
                'difficulty': p.difficulty or 'Easy',  # 保持原始格式（Easy/Medium/Hard）
                'description': p.description or '',
                'tag': p.tag or '',
                'database_name': p.database_name or '',
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in problems]
            return Response(data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching problems from GCP: {e}")
            return Response({'error': f'Failed to fetch problems: {str(e)}'}, status=500)
    
    elif request.method == 'POST':
        title = request.data.get('title')
        description = request.data.get('description')
        difficulty = request.data.get('difficulty', 'easy')
        schema_id = request.data.get('schema_id')
        expected_sql = request.data.get('expected_sql', '')
        initial_query = request.data.get('initial_query', '')
        
        if not title or not description:
            return Response({'error': 'Title and description required'}, status=400)
        
        schema = get_object_or_404(DatabaseSchema, id=schema_id) if schema_id else None
        
        exercise = Exercise.objects.create(
            title=title,
            description=description,
            difficulty=difficulty,
            schema=schema,
            expected_sql=expected_sql,
            initial_query=initial_query
        )
        
        return Response({
            'id': exercise.id,
            'title': exercise.title,
            'message': 'Exercise created successfully'
        }, status=201)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def instructor_exercise_detail(request, exercise_id):
    """
    PUT /api/instructor/exercises/{id}/ - 更新练习
    DELETE /api/instructor/exercises/{id}/ - 删除练习
    """
    
    if not check_instructor(request.user):
        return Response({'error': 'Unauthorized'}, status=403)
    
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    if request.method == 'PUT':
        exercise.title = request.data.get('title', exercise.title)
        exercise.description = request.data.get('description', exercise.description)
        exercise.difficulty = request.data.get('difficulty', exercise.difficulty)
        exercise.expected_sql = request.data.get('expected_sql', exercise.expected_sql)
        exercise.save()
        
        return Response({
            'id': exercise.id,
            'title': exercise.title,
            'message': 'Exercise updated successfully'
        })
    
    elif request.method == 'DELETE':
        exercise.delete()
        return Response({'message': 'Exercise deleted successfully'}, status=204)