from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CitySearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-searched_at']

    def __str__(self):
        return f"{self.user.username} - {self.city_name}"


class WeatherTask(models.Model):
    TASK_TYPES = [
        ('rain', 'Дождь'),
        ('cold', 'Холод'),
        ('hot', 'Жара'),
        ('wind', 'Ветер'),
        ('snow', 'Снег'),
        ('general', 'Общее'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='general')
    city = models.CharField(max_length=100)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class WeatherCache(models.Model):
    city_name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100)
    temperature = models.FloatField()
    humidity = models.IntegerField()
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=50)
    weather_data = models.JSONField(default=dict)
    cached_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return (timezone.now() - self.cached_at).total_seconds() > 7200

    def __str__(self):
        return f"{self.city_name} - {self.temperature}°C"