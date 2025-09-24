from django.urls import path
from . import views


urlpatterns = [
path('', views.dashboard, name='dashboard'),
path('tasks/', views.task_list, name='task_list'),
path('tasks/create/', views.task_create, name='task_create'),
path('tasks/<int:pk>/edit/', views.task_update, name='task_update'),
path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
]