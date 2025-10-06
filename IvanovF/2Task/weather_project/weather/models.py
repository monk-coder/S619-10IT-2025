from django.conf import settings
from django.db import models
from django.utils import timezone


class SearchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weather_search_history",
    )
    city = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.city} (@{self.user})"


class WeatherTask(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weather_tasks",
    )
    city = models.CharField(max_length=128)
    text = models.TextField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - readable representation
        return f"{self.city}: {self.text[:50]} (@{self.user})"


class WeatherSnapshot(models.Model):
    city = models.CharField(max_length=128)
    normalized_city = models.CharField(max_length=128, unique=True)
    payload = models.JSONField()
    fetched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-fetched_at"]

    def refresh(self, city: str, payload: dict) -> None:
        self.city = city[:128]
        self.payload = payload
        self.fetched_at = timezone.now()
        self.save(update_fields=["city", "payload", "fetched_at"])
