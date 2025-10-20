from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CitySearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    searched_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.city_name} searched by {self.user.username}"


class WeatherTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    task_text = models.TextField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.task_text} in {self.city_name} for {self.user.username}"


class FavoriteCity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'city_name']

    def __str__(self):
        return f"{self.city_name} - {self.user.username}"


class UserProfile(models.Model):
    LANGUAGES = [
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
    THEMES = [
        ('light', 'Светлая'),
        ('dark', 'Тёмная'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=LANGUAGES, default='ru')
    theme = models.CharField(max_length=10, choices=THEMES, default='light')

    def __str__(self):
        return f"Profile of {self.user.username}"


class WeatherCache(models.Model):
    city_name = models.CharField(max_length=100, unique=True)
    weather_data = models.JSONField()
    cached_at = models.DateTimeField(default=timezone.now)

    def is_valid(self):
        """Проверяет, актуальны ли данные (не старше 2 часов)"""
        return (timezone.now() - self.cached_at).total_seconds() < 7200  # 2 часа

    def __str__(self):
        return f"Weather cache for {self.city_name}"


# Сигналы для автоматического создания профиля
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()