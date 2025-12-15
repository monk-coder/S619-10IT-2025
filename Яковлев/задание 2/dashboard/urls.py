# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('weather-rules/', views.weather_rules, name='weather_rules'),
    path('toggle-rule/<int:rule_id>/', views.toggle_rule, name='toggle_rule'),
    path('delete-rule/<int:rule_id>/', views.delete_rule, name='delete_rule'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('toggle-task/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('toggle-task-ajax/<int:task_id>/', views.toggle_task_ajax, name='toggle_task_ajax'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('clear-history/', views.clear_history, name='clear_history'),
]