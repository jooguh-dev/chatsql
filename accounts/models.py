from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password, check_password
import uuid


class CustomUser(models.Model):
    """
    映射 GCP chatsql_system 数据库中的 user 表
    
    表结构：
    - id: int, auto_increment, primary key
    - username: varchar(50), unique, not null
    - email: varchar(255), unique, not null
    - password_hash: varchar(255), not null
    - is_admin: tinyint(1), default 0
    - created_at: timestamp, default CURRENT_TIMESTAMP
    """
    id = models.AutoField(primary_key=True, db_column='id')
    username = models.CharField(max_length=50, unique=True, db_column='username')
    email = models.CharField(max_length=255, unique=True, db_column='email')
    password_hash = models.CharField(max_length=255, db_column='password_hash')
    is_admin = models.BooleanField(default=False, db_column='is_admin')
    # created_at 在数据库中有默认值，Django 不自动设置
    created_at = models.DateTimeField(db_column='created_at', null=True, blank=True, auto_now_add=False)
    
    def __str__(self):
        return f"{self.username} ({'admin' if self.is_admin else 'user'})"
    
    def set_password(self, raw_password):
        """设置密码（自动哈希）"""
        self.password_hash = make_password(raw_password)
    
    def check_password(self, raw_password):
        """验证密码"""
        return check_password(raw_password, self.password_hash)
    
    @property
    def role(self):
        """根据 is_admin 返回角色"""
        return 'instructor' if self.is_admin else 'student'
    
    class Meta:
        db_table = 'users'  # 表名是 users 不是 user
        managed = False  # 表已存在于数据库中，Django 不管理迁移


class UserProfile(models.Model):
    """
    保留用于向后兼容，但主要使用 CustomUser
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    student_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        db_table = 'user_profile'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # superuser 自动是 instructor，否则是 student
        role = 'instructor' if instance.is_superuser else 'student'
        UserProfile.objects.create(user=instance, role=role)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # 确保 profile 存在
    if hasattr(instance, 'profile'):
        # 同步 superuser 状态
        if instance.is_superuser and instance.profile.role != 'instructor':
            instance.profile.role = 'instructor'
            instance.profile.save()