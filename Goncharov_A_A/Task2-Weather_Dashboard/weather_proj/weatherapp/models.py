from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.postgres.fields import JSONField if False else models.JSONField


class Task(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    city = models.CharField(max_length=100)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    remind_on = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"{self.city}: {self.text[:30]}"


class CitySearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    city = models.CharField(max_length=100)
    searched_at = models.DateTimeField(default=timezone.now)


    class Meta:
        ordering = ['-searched_at']


    def __str__(self):
        return f"{self.user.username} - {self.city} @ {self.searched_at}"


class CachedWeather(models.Model):
    city = models.CharField(max_length=100, unique=True)
    data = models.JSONField()
    fetched_at = models.DateTimeField()


    def is_old(self):
        return (timezone.now() - self.fetched_at).total_seconds() > 2 * 3600


    def __str__(self):
        return f"Cached {self.city} @ {self.fetched_at}"