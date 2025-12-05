from django.urls import path, include
from exercises.admin import admin_site
from exercises.views import (
    SchemaListView,
    ExerciseListView,
    ExerciseDetailView,
    ExecuteQueryView,
    SubmitQueryView,
    SubmissionListView,
)
from ai_tutor.views import ExerciseAIView
from accounts.views import (
    me,
    instructor_stats,
    instructor_students,
    instructor_student_detail,
    instructor_recent_activity,
)
# Exercise management 从 exercises 导入
from exercises.views import (
    instructor_exercises,
    instructor_exercise_detail,
)

urlpatterns = [
    path('admin/', admin_site.urls),  # 使用自定义admin site
    
    # Exercise APIs
    path('api/schemas/', SchemaListView.as_view(), name='schema-list'),
    path('api/exercises/', ExerciseListView.as_view(), name='exercise-list'),
    path('api/exercises/<int:exercise_id>/', ExerciseDetailView.as_view(), name='exercise-detail'),
    path('api/exercises/<int:exercise_id>/execute/', ExecuteQueryView.as_view(), name='execute-query'),
    path('api/exercises/<int:exercise_id>/submit/', SubmitQueryView.as_view(), name='submit-query'),
    path('api/exercises/<int:exercise_id>/submissions/', SubmissionListView.as_view(), name='submission-list'),
    path('api/exercises/<int:exercise_id>/ai/', ExerciseAIView.as_view(), name='exercise-ai'),
    
    # Auth APIs
    path('api/auth/', include('accounts.urls')),
    path('api/auth/me/', me, name='current-user'),
    
    # Instructor APIs
    path('api/instructor/stats/', instructor_stats, name='instructor-stats'),
    path('api/instructor/students/', instructor_students, name='instructor-students'),
    path('api/instructor/students/<int:student_id>/', instructor_student_detail, name='instructor-student-detail'),
    path('api/instructor/recent-activity/', instructor_recent_activity, name='instructor-recent-activity'),
    path('api/instructor/exercises/', instructor_exercises, name='instructor-exercises'),
    path('api/instructor/exercises/<int:exercise_id>/', instructor_exercise_detail, name='instructor-exercise-detail'),
    
    # Frontend
]