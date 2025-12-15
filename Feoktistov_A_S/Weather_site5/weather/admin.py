from django.contrib import admin
from .models import UserProfile, SearchHistory, UserNote


# Регистрируем модели для админки

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'favorite_city', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'favorite_city')
    date_hierarchy = 'created_at'


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'temperature', 'description', 'searched_at')
    list_filter = ('searched_at', 'city')
    search_fields = ('user__username', 'city', 'description')
    date_hierarchy = 'searched_at'
    readonly_fields = ('searched_at',)


@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'title', 'content')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    # Показываем содержимое заметки в админке
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'content')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )