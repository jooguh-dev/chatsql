from django.db import models
from django.contrib.auth.models import User

class DatabaseSchema(models.Model):
    """
    数据库架构定义
    - GCP环境: db_name应为 'chatsql_problem_N' (如 'chatsql_problem_1', 'chatsql_problem_2')
    - Legacy环境: db_name可为 'practice_hr', 'practice_ecommerce', 'practice_school'
    """
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    db_name = models.CharField(max_length=50)  # chatsql_problem_N (GCP) 或 practice_* (legacy)
    schema_sql = models.TextField(help_text="CREATE TABLE statements")
    seed_sql = models.TextField(help_text="INSERT sample data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name

    class Meta:
        db_table = 'database_schemas'

class Exercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    schema = models.ForeignKey(DatabaseSchema, on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    order = models.IntegerField(default=0)
    expected_sql = models.TextField(help_text="Reference solution")
    initial_query = models.TextField(blank=True, help_text="Starter code for students")
    hints = models.JSONField(default=list, help_text='[{"level": 1, "text": "hint1"}, ...]')
    tags = models.JSONField(default=list, help_text='["JOIN", "GROUP BY", "Subquery"]')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.schema.name} - {self.title}"

    class Meta:
        db_table = 'exercises'
        ordering = ['order', 'id']

class UserProgress(models.Model):
    """Track user progress (anonymous via session_id or authenticated via user)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=64, db_index=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    last_query = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_progress'
        unique_together = [['session_id', 'exercise']]

class ChatHistory(models.Model):
    """Store AI chat conversations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=64, db_index=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    response = models.TextField()
    context = models.JSONField(default=dict, help_text='{"query": "...", "error": "..."}')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_history'
        ordering = ['-created_at']

class Submission(models.Model):
    """Track student submissions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('correct', 'Correct'),
        ('incorrect', 'Incorrect'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='submissions')
    query = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    execution_time = models.FloatField(null=True, blank=True, help_text='Query execution time in seconds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise.title} - {self.status}"
    
    class Meta:
        db_table = 'submissions'
        ordering = ['-created_at']


class Problem(models.Model):
    """
    映射 GCP chatsql_system 数据库中的 problems 表
    
    表结构：
    - id: bigint, primary key
    - title: varchar(255), not null
    - difficulty: varchar(50), nullable (Easy, Medium, Hard)
    - tag: varchar(255), nullable
    - description: text, nullable
    - database_name: varchar(255), nullable (如 'chatsql_problem_1')
    - expected_query: longtext, nullable
    - expected_result: longtext, nullable
    - created_at: timestamp, nullable
    """
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
        ('easy', 'easy'),
        ('medium', 'medium'),
        ('hard', 'hard'),
    ]
    
    id = models.BigIntegerField(primary_key=True, db_column='id')
    title = models.CharField(max_length=255, db_column='title')
    difficulty = models.CharField(max_length=50, db_column='difficulty', null=True, blank=True, choices=DIFFICULTY_CHOICES)
    tag = models.CharField(max_length=255, db_column='tag', null=True, blank=True)
    description = models.TextField(db_column='description', null=True, blank=True)
    database_name = models.CharField(max_length=255, db_column='database_name', null=True, blank=True)
    expected_query = models.TextField(db_column='expected_query', null=True, blank=True)
    expected_result = models.TextField(db_column='expected_result', null=True, blank=True)
    created_at = models.DateTimeField(db_column='created_at', null=True, blank=True)
    
    def __str__(self):
        return f"{self.id}: {self.title}"
    
    @property
    def difficulty_lower(self):
        """返回小写的difficulty，用于兼容"""
        if self.difficulty:
            return self.difficulty.lower()
        return 'easy'
    
    class Meta:
        db_table = 'problems'
        managed = False  # 表已存在于数据库中，Django 不管理迁移
        ordering = ['id']