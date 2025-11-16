from django.db import models
from django.contrib.auth.models import User

class WeatherTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="Название задачи")
    description = models.TextField(blank=True, verbose_name="Описание")
    related_city = models.CharField(max_length=100, blank=True, verbose_name="Связанный город")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнена")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

class CitySearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100, verbose_name="Название города")
    country = models.CharField(max_length=100, verbose_name="Страна")
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city_name}, {self.country}"

    class Meta:
        verbose_name = "История поиска"
        verbose_name_plural = "Истории поиска"