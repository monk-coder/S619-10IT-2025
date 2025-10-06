from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/weather/", views.get_weather, name="get_weather"),
    path("api/flight/", views.get_flight, name="get_flight"),
    path("api/time/", views.get_time, name="get_time"),   # <-- новый эндпоинт
    path("api/auth/register/", views.register_user, name="register_user"),
    path("api/auth/login/", views.login_user, name="login_user"),
    path("api/auth/logout/", views.logout_user, name="logout_user"),
    path("api/auth/status/", views.auth_status, name="auth_status"),
    path("api/history/", views.get_history, name="get_history"),
    path("api/tasks/", views.tasks_collection, name="tasks_collection"),
    path("api/tasks/<int:task_id>/", views.task_detail, name="task_detail"),

]
