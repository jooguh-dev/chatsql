import os
import re
from django.conf import settings
from anthropic import Anthropic

# Configure API key
API_KEY = os.getenv('ANTHROPIC_API_KEY') or getattr(settings, 'ANTHROPIC_API_KEY', None)


def _mock_response(message: str, exercise, user_query: str = None, error: str = None, submissions: list = None) -> dict:
    """Return a short canned response for demo/mock mode."""
    ex_title = getattr(exercise, 'title', 'this exercise') if exercise is not None else 'the exercise'
    
    # Detect if message looks like a data query
    query_keywords = ['how many', 'show me', 'find', 'list', 'count', 'what is my', 'my progress', 'did i solve']
    is_data_query = any(keyword in message.lower() for keyword in query_keywords)
    
    if is_data_query:
        # Mock SQL generation and execution
        return {
            'response': "Based on your question, here's what I found: You have completed 3 exercises this month. (mock data)",
            'sql_query': "SELECT COUNT(*) FROM submissions WHERE user_id=1 AND status='correct' AND MONTH(created_at)=MONTH(CURRENT_DATE)",
            'should_execute': True,
            'intent': 'data_query'
        }
    
    # Regular tutoring response
    if error:
        response_text = f"I see an error: {error}. Check your SELECT columns and WHERE clause for typos."
    elif user_query:
        response_text = f"Your query looks reasonable for {ex_title}. Consider ordering results or selecting explicit columns."
    else:
        response_text = f"Try selecting the relevant columns from the table for {ex_title}."
    
    # 如果有submissions，在响应中提及
    if submissions and len(submissions) > 0:
        correct_count = sum(1 for s in submissions if s.get('status') == 'correct')
        response_text += f"\n\nYou have {len(submissions)} submission(s) for this problem ({correct_count} correct)."
    
    return {
        'response': response_text,
        'sql_query': None,
        'should_execute': False,
        'intent': 'tutoring'
    }


def _build_student_prompt(user_id: int, exercise=None, submissions=None, problem_database_name=None) -> str:
    """Build student-specific system prompt."""
    
    # 构建当前problem信息
    problem_info = ""
    if exercise:
        problem_info = f"""
**Current Problem:**
- ID: {getattr(exercise, 'id', 'N/A')}
- Title: {getattr(exercise, 'title', 'N/A')}
- Description: {getattr(exercise, 'description', 'N/A')[:200] if getattr(exercise, 'description', None) else 'N/A'}
- Difficulty: {getattr(exercise, 'difficulty', 'N/A')}
"""
    
    # 构建submissions历史信息
    submissions_info = ""
    if submissions and len(submissions) > 0:
        submissions_info = f"""
**User's Submission History for Current Problem:**
"""
        # 只显示最近5条提交记录
        recent_submissions = submissions[-5:] if len(submissions) > 5 else submissions
        for i, sub in enumerate(recent_submissions, 1):
            status_emoji = "✅" if sub.get('status') == 'correct' else "❌"
            submissions_info += f"""
{i}. {status_emoji} Status: {sub.get('status', 'unknown')}
   Query: {sub.get('query', '')[:100]}{'...' if len(sub.get('query', '')) > 100 else ''}
   Time: {sub.get('created_at', 'N/A')}
"""
        if len(submissions) > 5:
            submissions_info += f"\n(Showing {len(recent_submissions)} of {len(submissions)} total submissions)\n"
    else:
        submissions_info = "\n**User's Submission History:** No submissions yet for this problem.\n"
    
    return f"""You are an intelligent SQL tutor assistant for students. Analyze the user's message and determine the intent:

**IMPORTANT: Keep responses SHORT and CONCISE. Aim for 2-3 sentences maximum unless the user asks for detailed explanation.**

**Intent Types:**
1. DATA_QUERY - User wants to check their own statistics/progress
2. TUTORING - User needs explanation of SQL concepts
3. DEBUG - User needs help fixing their query

**For DATA_QUERY:**
- Generate executable SQL to query the student's data
- Mark response with [SQL_QUERY] tag
- Include brief explanation (1-2 sentences only)
- Always filter by user_id={user_id}

**For TUTORING/DEBUG:**
- Provide clear, concise explanation (2-3 sentences maximum)
- Give brief examples when helpful (1 example only)
- Reference the current problem and user's past submissions when relevant
- No SQL generation needed
- Be direct and to the point - avoid lengthy explanations

{problem_info}

{submissions_info}

**Database Structure:**
The system uses multiple databases:
1. **chatsql_system** database (system tables):
   - `submissions`: (id, user_id, exercise_id, query, status, created_at)
     - status values: 'correct', 'incorrect', 'pending'
     - Use this database when querying submissions or user progress
   - `problems`: (id, title, description, difficulty, database_name, ...)
   - `problem_tables`: (problem_id, table_name, table_schema, ...)

2. **chatsql_problem_N** databases (problem-specific tables):
   - Each problem has its own database (e.g., chatsql_problem_1, chatsql_problem_2)
   - The actual problem tables (like Products, Customers, etc.) are in these databases
   - Current problem database: {problem_database_name or 'N/A'}

**Important Rules for SQL Queries:**
- When querying `submissions`, `problems`, or `problem_tables` tables, use `chatsql_system` database
- When querying problem-specific tables (like Products, Customers, etc.), use the corresponding `chatsql_problem_N` database
- The system will automatically route queries to the correct database based on the table names

**Student can query:**
- Their submission history (from `chatsql_system.submissions`)
- Their progress statistics (from `chatsql_system.submissions`)
- Problems they haven't solved (from `chatsql_system.problems` and `chatsql_system.submissions`)
- Their performance over time (from `chatsql_system.submissions`)

**When helping with the current problem:**
- Reference the problem description and requirements
- Look at past submissions to understand what the user has tried
- If previous submissions were incorrect, help identify the issue
- If previous submissions were correct, acknowledge their success

**Examples (Keep responses SHORT):**

User: "How many problems did I solve this month?"
Response:
[SQL_QUERY]
SELECT COUNT(*) FROM submissions 
WHERE user_id={user_id} 
AND status='correct' 
AND MONTH(created_at) = MONTH(CURRENT_DATE)
AND YEAR(created_at) = YEAR(CURRENT_DATE)

This counts your correct submissions from the current month.

---

User: "What's the difference between INNER JOIN and LEFT JOIN?"
Response:
INNER JOIN returns only matching rows. LEFT JOIN returns all left rows plus matches (with NULLs for non-matches). Example: INNER shows only students with submissions; LEFT shows all students.
"""


def _extract_sql_from_response(response_text: str) -> tuple[str, str]:
    """Extract SQL query and intent from AI response."""
    
    # Check for SQL marker
    if '[SQL_QUERY]' not in response_text:
        return None, 'tutoring'
    
    # Extract SQL (look for SELECT/UPDATE/INSERT)
    sql_pattern = r'(SELECT|UPDATE|INSERT|DELETE)\s+[\s\S]*?(?=\n\n|\Z)'
    match = re.search(sql_pattern, response_text, re.IGNORECASE | re.MULTILINE)
    
    if match:
        sql_query = match.group(0).strip()
        # Clean up markdown formatting
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        # Remove trailing explanation
        sql_query = sql_query.split('\n\n')[0].strip()
        return sql_query, 'data_query'
    
    return None, 'tutoring'


def get_ai_response(
    message: str, 
    exercise=None, 
    user_query: str = None, 
    error: str = None,
    user_role: str = 'student',
    user_id: int = None,
    submissions: list = None,
    problem_database_name: str = None
) -> dict:
    """Get AI tutor response for students with SQL generation capability.
    
    Returns dict:
    {
        'response': str,
        'sql_query': str | None,
        'should_execute': bool,
        'intent': str
    }
    """
    mode = getattr(settings, 'ANTHROPIC_MODE', 'mock')
    
    # Mock mode
    if mode != 'real':
        return _mock_response(message, exercise, user_query, error, submissions)
    
    # Real mode
    if not API_KEY:
        return {
            'response': "AI tutor is not configured (missing ANTHROPIC_API_KEY).",
            'sql_query': None,
            'should_execute': False,
            'intent': 'error'
        }
    
    if not user_id:
        return {
            'response': "User ID is required for AI assistance.",
            'sql_query': None,
            'should_execute': False,
            'intent': 'error'
        }
    
    # Build student prompt with exercise and submissions context
    system_prompt = _build_student_prompt(user_id, exercise=exercise, submissions=submissions, problem_database_name=problem_database_name)
    
    # Build user message with context
    user_prompt = f"User message: {message}"
    if exercise:
        user_prompt += f"\nCurrent exercise: {getattr(exercise, 'title', None)}"
        user_prompt += f"\nDifficulty: {getattr(exercise, 'difficulty', None)}"
        if hasattr(exercise, 'description') and exercise.description:
            user_prompt += f"\nProblem description: {exercise.description[:300]}"
    if user_query:
        user_prompt += f"\nStudent's SQL attempt: {user_query}"
    if error:
        user_prompt += f"\nExecution error: {error}"
    if submissions and len(submissions) > 0:
        user_prompt += f"\n\nUser has {len(submissions)} previous submission(s) for this problem."
    
    try:
        # Create Anthropic client
        client = Anthropic(api_key=API_KEY)
        
        response = client.messages.create(
            model='claude-3-haiku-20240307',
            max_tokens=300, 
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract response
        if not response.content:
            return {
                'response': "AI returned no content.",
                'sql_query': None,
                'should_execute': False,
                'intent': 'error'
            }
        
        # Anthropic returns content as a list of text blocks
        response_text = response.content[0].text.strip()
        
        # Parse response for SQL and intent
        sql_query, intent = _extract_sql_from_response(response_text)
        
        # Replace user_id placeholder if present
        if sql_query and '{user_id}' in sql_query:
            sql_query = sql_query.replace('{user_id}', str(user_id))
        
        # Auto-execute data queries
        should_execute = (intent == 'data_query' and sql_query is not None)
        
        return {
            'response': response_text,
            'sql_query': sql_query,
            'should_execute': should_execute,
            'intent': intent
        }
        
    except Exception as e:
        return {
            'response': f"AI tutor encountered an error: {str(e)}. Please try rephrasing your question.",
            'sql_query': None,
            'should_execute': False,
            'intent': 'error'
        }