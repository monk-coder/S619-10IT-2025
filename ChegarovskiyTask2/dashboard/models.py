from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class CitySearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    searched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-searched_at']

    def __str__(self):
        return f"{self.user.username} - {self.city_name}"

class WeatherTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    task_text = models.TextField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.city_name} - {self.task_text[:20]}"

class FavoriteCity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-added_at']
        unique_together = ['user', 'city_name']

    def __str__(self):
        return f"{self.user.username} - {self.city_name}"

class UserProfile(models.Model):
    THEMES = [
        ('light', 'Светлая'),
        ('dark', 'Тёмная'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, choices=THEMES, default='light')

    def __str__(self):
        return f"Profile - {self.user.username}"

class WeatherCache(models.Model):
    city_name = models.CharField(max_length=100, unique=True)
    weather_data = models.JSONField()
    cached_at = models.DateTimeField(default=timezone.now)

    def is_valid(self):
        return (timezone.now() - self.cached_at).total_seconds() < 7200

    def __str__(self):
        return f"Cache - {self.city_name}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
