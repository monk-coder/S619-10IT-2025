from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TelegramUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_subscribed = models.BooleanField(default=True)
    language_code = models.CharField(max_length=10, default='ru')
    
    def __str__(self):
        return f"{self.username or self.telegram_id} ({self.first_name})"
    
    class Meta:
        verbose_name = 'Telegram пользователь'
        verbose_name_plural = 'Telegram пользователи'

class UserCity(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'city']
        verbose_name = 'Город пользователя'
        verbose_name_plural = 'Города пользователей'