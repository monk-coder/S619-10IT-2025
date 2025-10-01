from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/weather/", views.get_weather, name="get_weather"),
    path("api/flight/", views.get_flight, name="get_flight"),
    path("api/time/", views.get_time, name="get_time"),   # <-- новый эндпоинт

]
