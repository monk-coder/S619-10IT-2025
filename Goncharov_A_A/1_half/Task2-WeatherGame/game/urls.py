from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "game"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("", views.index, name="index"),

    path("api/game/state/", views.api_game_state, name="api_game_state"),
    path("api/game/progress/", views.api_game_progress, name="api_game_progress"),
    path("api/game/reset/", views.api_game_reset, name="api_game_reset"),
    path("api/weather/lookup/", views.api_weather_lookup, name="api_weather_lookup"),
    path("api/weather/history/", views.api_weather_history, name="api_weather_history"),
    path("api/upgrades/", views.api_upgrades, name="api_upgrades"),
    path("api/tasks/", views.api_tasks, name="api_tasks"),
    path("api/tasks/<int:task_id>/", views.api_task_detail, name="api_task_detail"),
]
