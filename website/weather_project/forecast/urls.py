from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    # URLs для управления историей поиска
    path('clear-history/', views.clear_search_history, name='clear_search_history'),
    path('remove-search-item/<str:city_name>/', views.remove_search_item, name='remove_search_item'),

    # URLs для заметок
    path('notes/', views.note_list, name='note_list'),
    path('notes/create/', views.note_create, name='note_create'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),

    # URL для админ-панели на сайте
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]