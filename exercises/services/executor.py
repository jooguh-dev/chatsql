import pymysql
import time
import os
from typing import Dict, List, Tuple
from django.conf import settings

class SQLExecutor:
    """Secure SQL query executor for practice databases"""
    
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
        'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC'
    ]
    
    MAX_EXECUTION_TIME = 5  # seconds
    MAX_ROWS = 1000
    
    def __init__(self, db_name: str):
        """
        Initialize executor for specific practice database
        Args:
            db_name: 
                - For GCP: 'chatsql_problem_N' (e.g., 'chatsql_problem_1', 'chatsql_problem_2')
                - For legacy: 'practice_hr', 'practice_ecommerce', or 'practice_school'
        """
        # 检查是否是GCP环境
        gcp_db_host = os.getenv('GCP_DB_HOST')
        
        if gcp_db_host:
            # GCP Cloud SQL环境：动态构建数据库配置
            if db_name.startswith('chatsql_problem_'):
                # 动态题目数据库
                self.db_config = self._get_gcp_db_config(db_name)
            elif db_name in settings.DATABASES:
                # 使用settings中已定义的数据库（如chatsql_system）
                self.db_config = settings.DATABASES[db_name]
            else:
                raise ValueError(f"Invalid database for GCP: {db_name}")
        else:
            # 传统环境：从settings.DATABASES获取
            if db_name not in settings.DATABASES:
                raise ValueError(f"Invalid database: {db_name}")
            self.db_config = settings.DATABASES[db_name]
        
        self.db_name = db_name
    
    def _get_gcp_db_config(self, db_name: str) -> Dict:
        """动态生成GCP Cloud SQL数据库配置"""
        return {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': db_name,
            'USER': os.getenv('GCP_DB_USER'),
            'PASSWORD': os.getenv('GCP_DB_PASSWORD'),
            'HOST': os.getenv('GCP_DB_HOST'),
            'PORT': os.getenv('GCP_DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            }
        }
    
    def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        Validate SQL query for security
        Returns: (is_valid, error_message)
        """
        query_upper = query.strip().upper()
        
        # Must start with SELECT
        if not query_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                return False, f"Keyword '{keyword}' is not allowed"
        
        # Check for comment-based injection
        if '--' in query or '/*' in query or '*/' in query:
            return False, "Comments are not allowed in queries"
        
        # Check for semicolon (multiple statements)
        if query.count(';') > 1:
            return False, "Multiple statements are not allowed"
        
        return True, ""
    
    def execute(self, query: str) -> Dict:
        """
        Execute SQL query and return results
        Returns: {
            'success': bool,
            'columns': List[str],
            'rows': List[List],
            'row_count': int,
            'execution_time': float,
            'error': str (if failed)
        }
        """
        # Validate query
        is_valid, error = self.validate_query(query)
        if not is_valid:
            return {
                'success': False,
                'error': error,
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time': 0
            }
        
        connection = None
        start_time = time.time()
        
        try:
            # Connect to database
            connection = pymysql.connect(
                host=self.db_config['HOST'],
                user=self.db_config['USER'],
                password=self.db_config['PASSWORD'],
                database=self.db_config['NAME'],
                port=int(self.db_config.get('PORT', 3306)),
                connect_timeout=5,
                read_timeout=self.MAX_EXECUTION_TIME,
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                # Execute query with timeout
                cursor.execute(query)
                
                # Fetch results (limited)
                rows = cursor.fetchmany(self.MAX_ROWS)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Convert to list of lists for JSON serialization
                row_list = [list(row.values()) for row in rows]
                
                execution_time = time.time() - start_time
                
                return {
                    'success': True,
                    'columns': columns,
                    'rows': row_list,
                    'row_count': len(row_list),
                    'execution_time': round(execution_time, 3),
                    'error': None
                }
        
        except pymysql.MySQLError as e:
            return {
                'success': False,
                'error': str(e),
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time': round(time.time() - start_time, 3)
            }
        
        finally:
            if connection:
                connection.close()
    
    def compare_results(self, user_result: Dict, expected_result: Dict) -> Dict:
        """
        Compare user query result with expected result
        Returns: {
            'correct': bool,
            'message': str,
            'diff': Dict (if incorrect)
        }
        """
        if not user_result['success']:
            return {
                'correct': False,
                'message': 'Query execution failed',
                'diff': None
            }
        
        # Compare column names (order doesn't matter)
        user_cols = set(user_result['columns'])
        expected_cols = set(expected_result['columns'])
        
        if user_cols != expected_cols:
            return {
                'correct': False,
                'message': 'Column names do not match',
                'diff': {
                    'missing_columns': list(expected_cols - user_cols),
                    'extra_columns': list(user_cols - expected_cols)
                }
            }
        
        # Compare row count
        if user_result['row_count'] != expected_result['row_count']:
            return {
                'correct': False,
                'message': f"Row count mismatch: expected {expected_result['row_count']}, got {user_result['row_count']}",
                'diff': None
            }
        
        # Compare actual data (normalize for comparison)
        user_data_normalized = self._normalize_result(user_result)
        expected_data_normalized = self._normalize_result(expected_result)
        
        if user_data_normalized != expected_data_normalized:
            return {
                'correct': False,
                'message': 'Query results do not match expected output',
                'diff': None
            }
        
        return {
            'correct': True,
            'message': 'Correct! Well done!',
            'diff': None
        }
    
    def _normalize_result(self, result: Dict) -> set:
        """Normalize result for comparison (handle row order)"""
        rows = []
        for row in result['rows']:
            # Convert each row to tuple (hashable) and sort
            row_tuple = tuple(sorted(str(val) for val in row))
            rows.append(row_tuple)
        return set(rows)
