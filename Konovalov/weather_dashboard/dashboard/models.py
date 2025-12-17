from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    searched_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-searched_at']
        verbose_name = 'История поиска'
        verbose_name_plural = 'Истории поиска'

    def __str__(self):
        return f"{self.user.username} - {self.city} - {self.searched_at}"

class WeatherTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    task_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Погодная задача'
        verbose_name_plural = 'Погодные задачи'

    def __str__(self):
        return f"{self.user.username} - {self.city}"

class WeatherCache(models.Model):
    city = models.CharField(max_length=100, unique=True)
    weather_data = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Кэш погоды'
        verbose_name_plural = 'Кэши погоды'

    def is_valid(self):
        return (timezone.now() - self.last_updated).total_seconds() < 7200  # 2 часа
    
    def __str__(self):
        return f"{self.city} - {self.last_updated}"