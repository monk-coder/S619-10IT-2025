from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
<<<<<<< HEAD

=======
from django.db.models.signals import post_save
from django.dispatch import receiver
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8

class CitySearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    searched_at = models.DateTimeField(default=timezone.now)

<<<<<<< HEAD
    def __str__(self):
        return f"{self.city_name} searched by {self.user.username}"

=======
    class Meta:
        ordering = ['-searched_at']

    def __str__(self):
        return f"{self.user.username} - {self.city_name}"
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8

class WeatherTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    task_text = models.TextField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

<<<<<<< HEAD
    def __str__(self):
        return f"{self.task_text} in {self.city_name} for {self.user.username}"

=======
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.city_name} - {self.task_text[:20]}"
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8

class FavoriteCity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
<<<<<<< HEAD
        unique_together = ['user', 'city_name']

    def __str__(self):
        return f"{self.city_name} - {self.user.username}"


class UserProfile(models.Model):
    LANGUAGES = [
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
=======
        ordering = ['-added_at']
        unique_together = ['user', 'city_name']

    def __str__(self):
        return f"{self.user.username} - {self.city_name}"

class UserProfile(models.Model):
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
    THEMES = [
        ('light', 'Светлая'),
        ('dark', 'Тёмная'),
    ]
<<<<<<< HEAD

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=LANGUAGES, default='ru')
    theme = models.CharField(max_length=10, choices=THEMES, default='light')

    def __str__(self):
        return f"Profile of {self.user.username}"

=======
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, choices=THEMES, default='light')

    def __str__(self):
        return f"Profile - {self.user.username}"
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8

class WeatherCache(models.Model):
    city_name = models.CharField(max_length=100, unique=True)
    weather_data = models.JSONField()
    cached_at = models.DateTimeField(default=timezone.now)

    def is_valid(self):
<<<<<<< HEAD
        """Проверяет, актуальны ли данные (не старше 2 часов)"""
        return (timezone.now() - self.cached_at).total_seconds() < 7200  # 2 часа

    def __str__(self):
        return f"Weather cache for {self.city_name}"


# Сигналы для автоматического создания профиля
from django.db.models.signals import post_save
from django.dispatch import receiver

=======
        return (timezone.now() - self.cached_at).total_seconds() < 7200

    def __str__(self):
        return f"Cache - {self.city_name}"
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

<<<<<<< HEAD

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
=======
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
