# dashboard/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import SearchHistory, WeatherTask, WeatherRule

# Регистрируем модели для управления в админке
@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'timestamp')
    list_filter = ('user', 'timestamp')
    search_fields = ('city', 'user__username')

@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'description', 'completed', 'created_at')
    list_filter = ('user', 'completed', 'city')
    search_fields = ('description', 'city', 'user__username')

@admin.register(WeatherRule)
class WeatherRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'condition_type', 'operator', 'threshold_value', 'is_active', 'created_at')
    list_filter = ('user', 'condition_type', 'is_active', 'created_at')
    search_fields = ('name', 'task_description', 'user__username')
    list_editable = ('is_active',)

# Расширяем стандартную админку пользователей
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')

# Перерегистрируем UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)