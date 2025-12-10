from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    searched_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-searched_at']

class WeatherTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    task_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class WeatherCache(models.Model):
    city = models.CharField(max_length=100, unique=True)
    weather_data = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
    
    def is_valid(self):
        return (timezone.now() - self.last_updated).total_seconds() < 7200  # 2 часа