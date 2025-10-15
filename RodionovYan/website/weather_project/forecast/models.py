from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class City(models.Model):
    """Модель для хранения городов"""
    name = models.CharField(max_length=100, verbose_name="Название города")
    country = models.CharField(max_length=100, verbose_name="Страна")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Широта")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Долгота")

    def __str__(self):
        return f"{self.name}, {self.country}"

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"


class WeatherData(models.Model):
    """Модель для хранения данных о погоде"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="Город")
    temperature = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Температура")
    description = models.CharField(max_length=200, verbose_name="Описание")
    humidity = models.IntegerField(verbose_name="Влажность")
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Скорость ветра")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время обновления")

    def __str__(self):
        return f"{self.city.name}: {self.temperature}°C"

    class Meta:
        verbose_name = "Данные погоды"
        verbose_name_plural = "Данные погоды"


class UserNote(models.Model):
    """Модель для заметок пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Заголовок заметки")
    content = models.TextField(verbose_name="Содержание заметки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время обновления")

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        verbose_name = "Заметка пользователя"
        verbose_name_plural = "Заметки пользователей"
        ordering = ['-created_at']