from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.db import connection
from exercises.models import Exercise, ChatHistory
from exercises.views import get_problem_from_gcp
from exercises.services.executor import SQLExecutor
from ai_tutor.services.openai_service import get_ai_response

@method_decorator(csrf_exempt, name='dispatch')
class ExerciseAIView(APIView):
    """POST /api/exercises/{id}/ai/ - Get AI help for students"""
    # permission_classes = [IsAuthenticated]

    def post(self, request, exercise_id):
        # 从GCP获取problem信息（优先），如果不存在则尝试从Django模型获取
        problem = get_problem_from_gcp(problem_id=exercise_id)
        problem_database_name = None  # 存储problem的数据库名
        
        if problem:
            # 创建一个类似Exercise的对象来传递problem信息
            class ProblemExercise:
                def __init__(self, problem_data):
                    self.id = problem_data['id']
                    self.title = problem_data['title']
                    self.description = problem_data.get('description', '')
                    self.difficulty = problem_data.get('difficulty', 'easy')
                    self.expected_query = problem_data.get('expected_query', '')
                    self.database_name = problem_data.get('database_name', '')  # 添加database_name属性
            
            exercise = ProblemExercise(problem)
            problem_database_name = problem.get('database_name')
        else:
            # Fallback: 尝试从Django模型获取
            try:
                exercise = get_object_or_404(Exercise, id=exercise_id)
                # 从schema获取database_name
                if hasattr(exercise, 'schema') and exercise.schema:
                    problem_database_name = exercise.schema.db_name
            except:
                return Response(
                    {'error': 'Exercise not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        message = request.data.get('message', '')
        user_query = request.data.get('user_query')
        error = request.data.get('error')
        submissions = request.data.get('submissions', [])  # 接收前端传递的submissions

        if not message and not user_query and not error:
            return Response(
                {'error': 'message or user_query or error is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 临时修复：使用假 user_id 或从 session 获取
        user_id = request.user.id if request.user.is_authenticated else 1
        # 从session获取user_id（如果存在）
        session_user_id = request.session.get('user_id')
        if session_user_id:
            user_id = session_user_id

        # Ensure session
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key

        # Get AI response (returns dict with sql_query, should_execute, etc.)
        ai_result = get_ai_response(
            message=message or user_query or 'Help me',
            exercise=exercise,
            user_query=user_query,
            error=error,
            user_role='student',  # Hard-coded for now, will use request.user.role later
            user_id=user_id,
            submissions=submissions,  # 传递submissions数据
            problem_database_name=problem_database_name  # 传递problem数据库名
        )

        response_data = {
            'response': ai_result['response'],
            'intent': ai_result['intent']
        }

        # If AI generated SQL and wants to execute it
        if ai_result['should_execute'] and ai_result['sql_query']:
            try:
                # Execute the AI-generated SQL in the correct database
                execution_result = self._execute_sql(ai_result['sql_query'], problem_database_name, exercise_id)
                
                response_data['sql_query'] = ai_result['sql_query']
                response_data['query_result'] = execution_result
                response_data['executed'] = True
                
                # Append result to response text
                result_summary = self._format_result_summary(execution_result)
                response_data['response'] = f"{ai_result['response']}\n\n{result_summary}"
                
            except Exception as e:
                response_data['sql_query'] = ai_result['sql_query']
                response_data['execution_error'] = str(e)
                response_data['executed'] = False
                response_data['response'] = f"{ai_result['response']}\n\n⚠️ Failed to execute query: {str(e)}"
        
        elif ai_result['sql_query'] and not ai_result['should_execute']:
            # SQL generated but not auto-executed (e.g., for teaching purposes)
            response_data['sql_query'] = ai_result['sql_query']
            response_data['executed'] = False

        # Persist ChatHistory (只有当exercise是Django模型实例时才保存)
        try:
            if isinstance(exercise, Exercise):
                ChatHistory.objects.create(
                    session_id=session_id,
                    exercise=exercise,
                    message=message or user_query or '',
                    response=response_data['response'],
                    context={
                        'user_query': user_query,
                        'error': error,
                        'ai_generated_sql': ai_result.get('sql_query'),
                        'intent': ai_result['intent']
                    }
                )
        except Exception as e:
            # 如果保存失败（例如exercise不是Django模型），记录但不影响响应
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to save chat history: {e}")

        return Response(response_data)

    def _execute_sql(self, sql_query: str, problem_database_name: str = None, exercise_id: int = None) -> dict:
        """
        Execute SQL query and return results.
        
        Args:
            sql_query: SQL query to execute
            problem_database_name: Database name for the problem (e.g., 'chatsql_problem_1')
            exercise_id: Exercise/Problem ID
        """
        # 判断SQL查询是针对哪个数据库的
        query_upper = sql_query.strip().upper()
        
        # 如果查询的是submissions表，使用chatsql_system数据库
        if 'submissions' in query_upper or 'exercises' in query_upper or 'problems' in query_upper:
            # 查询系统表，使用chatsql_system数据库
            with connection.cursor() as cursor:
                cursor.execute('USE chatsql_system')
                cursor.execute(sql_query)
                
                # Check if it's a SELECT query
                if query_upper.startswith('SELECT'):
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    return {
                        'success': True,
                        'columns': columns,
                        'rows': [list(row) for row in rows],
                        'row_count': len(rows)
                    }
                else:
                    # UPDATE/INSERT/DELETE
                    return {
                        'success': True,
                        'affected_rows': cursor.rowcount,
                        'message': f'{cursor.rowcount} row(s) affected'
                    }
        else:
            # 查询problem相关的表，使用对应的problem数据库
            if not problem_database_name:
                # 如果没有提供database_name，尝试从exercise_id获取
                if exercise_id:
                    problem = get_problem_from_gcp(problem_id=exercise_id)
                    if problem:
                        problem_database_name = problem.get('database_name')
                
                if not problem_database_name:
                    return {
                        'success': False,
                        'error': 'Cannot determine problem database. Please specify the problem.',
                        'columns': [],
                        'rows': [],
                        'row_count': 0
                    }
            
            # 使用SQLExecutor执行查询（它会连接到正确的problem数据库）
            try:
                executor = SQLExecutor(problem_database_name)
                result = executor.execute(sql_query)
                
                if result['success']:
                    return {
                        'success': True,
                        'columns': result['columns'],
                        'rows': result['rows'],
                        'row_count': result['row_count']
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Query execution failed'),
                        'columns': [],
                        'rows': [],
                        'row_count': 0
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'columns': [],
                    'rows': [],
                    'row_count': 0
                }

    def _format_result_summary(self, result: dict) -> str:
        """Format query result into readable text."""
        if not result['success']:
            return "❌ Query execution failed"
        
        if 'rows' in result:
            # SELECT result
            count = result['row_count']
            if count == 0:
                return "📊 Query executed successfully (0 results)"
            elif count == 1:
                return f"📊 Query returned 1 result"
            else:
                return f"📊 Query returned {count} results"
        else:
            # UPDATE/INSERT/DELETE result
            return f"✅ {result['message']}"