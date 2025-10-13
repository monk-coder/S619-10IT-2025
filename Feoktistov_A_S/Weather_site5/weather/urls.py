from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='weather_home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # ДОБАВЬ МАРШРУТЫ ДЛЯ ЗАМЕТОК
    path('note/edit/<int:note_id>/', views.edit_note, name='edit_note'),
    path('note/delete/<int:note_id>/', views.delete_note, name='delete_note'),
]