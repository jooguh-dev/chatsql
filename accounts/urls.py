from django.urls import path
from .views import signup, login, logout_view, me, profile, debug_user_table

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("login/", login, name="login"),
    path("logout/", logout_view, name="logout"),
    path("me/", me, name="me"),
    path("profile/", profile, name="profile"),
    path("debug/table/", debug_user_table, name="debug_user_table"),  # 调试端点
]
