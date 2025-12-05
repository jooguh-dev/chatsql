from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin import AdminSite, ModelAdmin
from django.http import JsonResponse
from .models import DatabaseSchema, Exercise, UserProgress, ChatHistory, Problem
from .admin_ai_service import get_ai_analytics_response, get_problem_statistics, get_overall_statistics


class DatabaseSchemaAdmin(ModelAdmin):
    list_display = ['name', 'display_name', 'db_name', 'created_at']
    search_fields = ['name', 'display_name']


class ExerciseAdmin(ModelAdmin):
    list_display = ['title', 'schema', 'difficulty', 'order', 'created_at']
    list_filter = ['schema', 'difficulty']
    search_fields = ['title', 'description']
    ordering = ['order', 'id']


class ProblemAdmin(ModelAdmin):
    """
    GCP problems表的admin界面
    映射到chatsql_system数据库的problems表
    """
    list_display = ['id', 'title', 'difficulty', 'tag', 'database_name', 'created_at']
    list_filter = ['difficulty', 'tag', 'database_name']
    search_fields = ['title', 'description', 'tag']
    ordering = ['id']
    readonly_fields = ['id', 'created_at']  # 这些字段通常是只读的
    
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'title', 'difficulty', 'tag', 'description')
        }),
        ('数据库配置', {
            'fields': ('database_name',)
        }),
        ('SQL配置', {
            'fields': ('expected_query', 'expected_result')
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )


class UserProgressAdmin(ModelAdmin):
    list_display = ['session_id', 'exercise', 'completed', 'attempts', 'completed_at']
    list_filter = ['completed', 'exercise__difficulty']
    search_fields = ['session_id']


class ChatHistoryAdmin(ModelAdmin):
    list_display = ['session_id', 'exercise', 'created_at']
    list_filter = ['created_at']
    search_fields = ['session_id', 'message']


# Custom Admin Site with AI Assistant
class ChatSQLAdminSite(AdminSite):
    site_header = "ChatSQL Admin"
    site_title = "ChatSQL Admin Portal"
    index_title = "Welcome to ChatSQL Administration"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('ai-assistant/', self.admin_view(self.ai_assistant_view), name='ai-assistant'),
            path('ai-assistant/query/', self.admin_view(self.ai_assistant_query), name='ai-assistant-query'),
        ]
        return custom_urls + urls
    
    def ai_assistant_view(self, request):
        """Custom admin view for AI Assistant"""
        context = {
            **self.each_context(request),
            'title': 'AI Analytics Assistant',
            'has_permission': self.has_permission(request),
            'opts': {'app_label': 'exercises', 'model_name': 'ai_assistant'},
        }
        return TemplateResponse(request, 'admin/ai_assistant.html', context)
    
    def ai_assistant_query(self, request):
        """Handle AI assistant query requests"""
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
        
        if not self.has_permission(request):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        import json
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            
            if not question:
                return JsonResponse({'error': 'Question is required'}, status=400)
            
            # 获取AI响应
            result = get_ai_analytics_response(question)
            
            return JsonResponse({
                'response': result.get('response', ''),
                'data': result.get('data'),
                'error': result.get('error')
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def index(self, request, extra_context=None):
        """Override index to add AI Assistant link"""
        extra_context = extra_context or {}
        extra_context['ai_assistant_url'] = self.reverse('ai-assistant')
        
        # 添加统计信息
        try:
            overall_stats = get_overall_statistics()
            extra_context['overall_stats'] = overall_stats
        except:
            pass
        
        return super().index(request, extra_context)


# 使用自定义admin site替换默认的
admin_site = ChatSQLAdminSite(name='admin')

# 注册所有模型到自定义admin site
from django.contrib.auth.models import User
admin_site.register(User)
admin_site.register(DatabaseSchema, DatabaseSchemaAdmin)
admin_site.register(Exercise, ExerciseAdmin)
admin_site.register(Problem, ProblemAdmin)
admin_site.register(UserProgress, UserProgressAdmin)
admin_site.register(ChatHistory, ChatHistoryAdmin)
