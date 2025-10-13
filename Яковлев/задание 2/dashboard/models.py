# dashboard/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    

class WeatherTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    completed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_automatic = models.BooleanField(default=False)
    weather_condition = models.CharField(max_length=50, blank=True)

class WeatherRule(models.Model):
    CONDITION_CHOICES = [
        ('temperature', 'Температура'),
        ('humidity', 'Влажность'),
        ('rain_probability', 'Вероятность дождя'),
        ('wind_speed', 'Скорость ветра'),
    ]
    
    OPERATOR_CHOICES = [
        ('gt', 'больше'),
        ('gte', 'больше или равно'),
        ('lt', 'меньше'),
        ('lte', 'меньше или равно'),
        ('eq', 'равно'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    condition_type = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES)
    threshold_value = models.FloatField()
    task_description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Правило погоды"
        verbose_name_plural = "Правила погоды"
    
    def __str__(self):
        return self.name