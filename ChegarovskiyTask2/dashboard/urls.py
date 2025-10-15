from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('task/update/<int:task_id>/', views.update_task_view, name='update_task'),
    path('task/delete/<int:task_id>/', views.delete_task_view, name='delete_task'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('favorites/remove/<int:city_id>/', views.remove_favorite_view, name='remove_favorite'),
    path('favorites/remove-by-name/', views.remove_favorite_by_name, name='remove_favorite_by_name'),
    path('settings/', views.settings_view, name='settings'),
]