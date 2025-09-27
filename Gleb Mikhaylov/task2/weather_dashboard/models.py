from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class WeatherTask(models.Model):
    """Модель для задач пользователей, связанных с погодой"""
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    title = models.CharField(max_length=200, verbose_name='Название задачи')
    description = models.TextField(blank=True, verbose_name='Описание')
    city = models.CharField(max_length=100, verbose_name='Город')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Срок выполнения')
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.city}"


class SearchHistory(models.Model):
    """Модель для истории поиска городов пользователями"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    city = models.CharField(max_length=100, verbose_name='Город')
    country = models.CharField(max_length=100, blank=True, verbose_name='Страна')
    searched_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата поиска')
    
    class Meta:
        verbose_name = 'История поиска'
        verbose_name_plural = 'История поиска'
        ordering = ['-searched_at']
        unique_together = ['user', 'city']
    
    def __str__(self):
        return f"{self.user.username} - {self.city}"


class WeatherCache(models.Model):
    """Модель для кэширования погодных данных"""
    city = models.CharField(max_length=100, verbose_name='Город')
    country = models.CharField(max_length=100, blank=True, verbose_name='Страна')
    temperature = models.FloatField(verbose_name='Температура')
    humidity = models.IntegerField(verbose_name='Влажность')
    description = models.CharField(max_length=200, verbose_name='Описание погоды')
    icon = models.CharField(max_length=10, verbose_name='Иконка')
    wind_speed = models.FloatField(verbose_name='Скорость ветра')
    pressure = models.IntegerField(verbose_name='Давление')
    cached_at = models.DateTimeField(auto_now_add=True, verbose_name='Время кэширования')
    
    class Meta:
        verbose_name = 'Кэш погоды'
        verbose_name_plural = 'Кэш погоды'
        ordering = ['-cached_at']
    
    def __str__(self):
        return f"{self.city} - {self.temperature}°C"
    
    def is_expired(self):
        """Проверяет, истек ли кэш"""
        from django.conf import settings
        from datetime import timedelta
        expiry_time = self.cached_at + timedelta(seconds=settings.WEATHER_CACHE_DURATION)
        return timezone.now() > expiry_time
