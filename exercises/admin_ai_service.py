"""
Admin AI Assistant Service
用于在Django admin界面回答关于题目统计的问题
"""
import os
from django.conf import settings
from django.db import connection
from anthropic import Anthropic

API_KEY = os.getenv('ANTHROPIC_API_KEY') or getattr(settings, 'ANTHROPIC_API_KEY', None)


def get_problem_statistics():
    """
    从GCP数据库获取所有问题的统计信息
    返回格式：
    [
        {
            'problem_id': int,
            'title': str,
            'total_submissions': int,
            'correct_submissions': int,
            'incorrect_submissions': int,
            'correct_rate': float,  # 0-100
            'difficulty': str,
            'tag': str
        },
        ...
    ]
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('USE chatsql_system')
            
            # 获取每个问题的统计信息
            cursor.execute("""
                SELECT 
                    p.id as problem_id,
                    p.title,
                    p.difficulty,
                    p.tag,
                    COUNT(s.id) as total_submissions,
                    SUM(CASE WHEN s.status = 'correct' THEN 1 ELSE 0 END) as correct_submissions,
                    SUM(CASE WHEN s.status = 'incorrect' THEN 1 ELSE 0 END) as incorrect_submissions
                FROM problems p
                LEFT JOIN submissions s ON p.id = s.exercise_id
                GROUP BY p.id, p.title, p.difficulty, p.tag
                ORDER BY p.id
            """)
            
            stats = []
            for row in cursor.fetchall():
                problem_id, title, difficulty, tag, total, correct, incorrect = row
                total = total or 0
                correct = correct or 0
                incorrect = incorrect or 0
                
                correct_rate = (correct / total * 100) if total > 0 else 0.0
                
                stats.append({
                    'problem_id': problem_id,
                    'title': title,
                    'total_submissions': total,
                    'correct_submissions': correct,
                    'incorrect_submissions': incorrect,
                    'correct_rate': round(correct_rate, 2),
                    'difficulty': difficulty or 'Unknown',
                    'tag': tag or ''
                })
            
            return stats
    except Exception as e:
        print(f"Error getting problem statistics: {e}")
        return []


def get_overall_statistics():
    """获取整体统计信息"""
    try:
        with connection.cursor() as cursor:
            cursor.execute('USE chatsql_system')
            
            # 总提交数
            cursor.execute('SELECT COUNT(*) FROM submissions')
            total_submissions = cursor.fetchone()[0] or 0
            
            # 正确提交数
            cursor.execute("SELECT COUNT(*) FROM submissions WHERE status = 'correct'")
            correct_submissions = cursor.fetchone()[0] or 0
            
            # 总问题数
            cursor.execute('SELECT COUNT(*) FROM problems')
            total_problems = cursor.fetchone()[0] or 0
            
            # 总用户数
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 0')
            total_students = cursor.fetchone()[0] or 0
            
            overall_rate = (correct_submissions / total_submissions * 100) if total_submissions > 0 else 0.0
            
            return {
                'total_submissions': total_submissions,
                'correct_submissions': correct_submissions,
                'incorrect_submissions': total_submissions - correct_submissions,
                'overall_correct_rate': round(overall_rate, 2),
                'total_problems': total_problems,
                'total_students': total_students
            }
    except Exception as e:
        print(f"Error getting overall statistics: {e}")
        return {}


def get_ai_analytics_response(question: str) -> dict:
    """
    使用AI回答关于题目统计的问题
    
    Args:
        question: 用户的问题，如 "which question has lowest correct rate"
    
    Returns:
        {
            'response': str,  # AI的回答
            'data': dict,     # 相关的统计数据（如果有）
            'error': str      # 错误信息（如果有）
        }
    """
    mode = getattr(settings, 'ANTHROPIC_MODE', 'mock')
    
    # 获取统计数据
    problem_stats = get_problem_statistics()
    overall_stats = get_overall_statistics()
    
    # Mock模式：返回简单的分析
    if mode != 'real':
        return _mock_analytics_response(question, problem_stats, overall_stats)
    
    # Real模式：使用AI分析
    if not API_KEY:
        return {
            'response': "AI助手未配置（缺少ANTHROPIC_API_KEY）。",
            'data': None,
            'error': 'missing_api_key'
        }
    
    try:
        # 构建系统提示
        system_prompt = _build_analytics_prompt(problem_stats, overall_stats)
        
        # 调用AI
        client = Anthropic(api_key=API_KEY)
        response = client.messages.create(
            model='claude-3-haiku-20240307',
            max_tokens=500,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": question}
            ]
        )
        
        response_text = response.content[0].text.strip() if response.content else "No response"
        
        # 尝试提取相关数据
        relevant_data = _extract_relevant_data(question, problem_stats)
        
        return {
            'response': response_text,
            'data': relevant_data,
            'error': None
        }
        
    except Exception as e:
        return {
            'response': f"AI助手遇到错误: {str(e)}",
            'data': None,
            'error': str(e)
        }


def _build_analytics_prompt(problem_stats: list, overall_stats: dict) -> str:
    """构建AI分析提示"""
    
    # 格式化问题统计数据
    stats_text = "\n".join([
        f"Problem {s['problem_id']}: {s['title']} "
        f"(Difficulty: {s['difficulty']}, Tag: {s['tag']}, "
        f"Total: {s['total_submissions']}, Correct: {s['correct_submissions']}, "
        f"Correct Rate: {s['correct_rate']}%)"
        for s in problem_stats
    ])
    
    overall_text = f"""
Overall Statistics:
- Total Problems: {overall_stats.get('total_problems', 0)}
- Total Students: {overall_stats.get('total_students', 0)}
- Total Submissions: {overall_stats.get('total_submissions', 0)}
- Correct Submissions: {overall_stats.get('correct_submissions', 0)}
- Overall Correct Rate: {overall_stats.get('overall_correct_rate', 0)}%
"""
    
    return f"""You are an analytics assistant for a SQL learning platform. You help instructors understand student performance data.

**Available Data:**

{overall_text}

**Problem Statistics:**
{stats_text}

**Your Task:**
Answer questions about student performance, problem difficulty, correct rates, etc. Be concise and specific. When asked about specific problems (e.g., "which question has lowest correct rate"), provide the problem ID, title, and relevant statistics.

**Response Format:**
- Be direct and concise
- Include specific numbers and problem IDs when relevant
- If asked about rankings (lowest/highest), list the top/bottom items
- Use Chinese for responses if the question is in Chinese, otherwise use English
"""


def _mock_analytics_response(question: str, problem_stats: list, overall_stats: dict) -> dict:
    """Mock模式的简单响应"""
    question_lower = question.lower()
    
    if 'lowest' in question_lower and 'correct rate' in question_lower:
        # 找到正确率最低的问题
        if problem_stats:
            sorted_stats = sorted(problem_stats, key=lambda x: x['correct_rate'])
            lowest = sorted_stats[0]
            return {
                'response': f"正确率最低的题目是：Problem {lowest['problem_id']}: {lowest['title']} "
                          f"(正确率: {lowest['correct_rate']}%, 总提交: {lowest['total_submissions']}, "
                          f"正确: {lowest['correct_submissions']}, 错误: {lowest['incorrect_submissions']})",
                'data': lowest,
                'error': None
            }
    
    elif 'highest' in question_lower and 'correct rate' in question_lower:
        # 找到正确率最高的问题
        if problem_stats:
            sorted_stats = sorted(problem_stats, key=lambda x: x['correct_rate'], reverse=True)
            highest = sorted_stats[0]
            return {
                'response': f"正确率最高的题目是：Problem {highest['problem_id']}: {highest['title']} "
                          f"(正确率: {highest['correct_rate']}%, 总提交: {highest['total_submissions']})",
                'data': highest,
                'error': None
            }
    
    elif 'overall' in question_lower or 'average' in question_lower:
        return {
            'response': f"整体统计：总提交数 {overall_stats.get('total_submissions', 0)}, "
                      f"正确率 {overall_stats.get('overall_correct_rate', 0)}%, "
                      f"总题目数 {overall_stats.get('total_problems', 0)}, "
                      f"总学生数 {overall_stats.get('total_students', 0)}",
            'data': overall_stats,
            'error': None
        }
    
    return {
        'response': f"这是一个mock响应。问题：{question}\n\n"
                   f"总共有 {len(problem_stats)} 个题目，"
                   f"总提交数 {overall_stats.get('total_submissions', 0)}。",
        'data': {'problem_count': len(problem_stats), **overall_stats},
        'error': None
    }


def _extract_relevant_data(question: str, problem_stats: list) -> dict:
    """从问题中提取相关数据"""
    question_lower = question.lower()
    
    if 'lowest' in question_lower and 'correct rate' in question_lower:
        if problem_stats:
            sorted_stats = sorted(problem_stats, key=lambda x: x['correct_rate'])
            return {'lowest_correct_rate': sorted_stats[0]}
    
    elif 'highest' in question_lower and 'correct rate' in question_lower:
        if problem_stats:
            sorted_stats = sorted(problem_stats, key=lambda x: x['correct_rate'], reverse=True)
            return {'highest_correct_rate': sorted_stats[0]}
    
    return None

