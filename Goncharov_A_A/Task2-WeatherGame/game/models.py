from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class PlayerState(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="player_state")
    current_floor = models.IntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)
    total_floors_travelled = models.PositiveIntegerField(default=0)
    last_weather_city = models.CharField(max_length=128, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"State<{self.user.email or self.user.username}>"


class PlayerUpgrade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="upgrades")
    upgrade_key = models.CharField(max_length=64)
    level = models.PositiveIntegerField(default=1)
    purchased_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "upgrade_key")

    def __str__(self) -> str:
        return f"Upgrade<{self.upgrade_key} x{self.level} for {self.user_id}>"


class WeatherSnapshot(models.Model):
    city = models.CharField(max_length=128, unique=True)
    payload = models.JSONField()
    fetched_at = models.DateTimeField()

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self) -> str:
        return f"Weather<{self.city} @ {timezone.localtime(self.fetched_at):%Y-%m-%d %H:%M}>"


class CitySearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="search_history")
    city = models.CharField(max_length=128)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-searched_at"]

    def __str__(self) -> str:
        return f"History<{self.city} for {self.user_id}>"


class TaskStatus(models.TextChoices):
    PENDING = "pending", "В ожидании"
    IN_PROGRESS = "in_progress", "В работе"
    DONE = "done", "Выполнена"


class WeatherTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weather_tasks")
    city = models.CharField(max_length=128)
    title = models.CharField(max_length=150)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Task<{self.title} ({self.city})>"
