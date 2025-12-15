from django.contrib import admin
from .models import TelegramUser, UserCity

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'username', 'first_name', 'is_subscribed', 'created_at']
    list_filter = ['is_subscribed', 'created_at']
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name']

@admin.register(UserCity)
class UserCityAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'is_favorite', 'created_at']
    list_filter = ['is_favorite', 'created_at']
    search_fields = ['user__username', 'city']