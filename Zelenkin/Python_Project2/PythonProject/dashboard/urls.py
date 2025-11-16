from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('task/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('task/toggle/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('history/clear/', views.clear_history, name='clear_history'),
]