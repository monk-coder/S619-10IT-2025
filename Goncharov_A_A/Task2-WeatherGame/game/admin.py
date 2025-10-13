from django.contrib import admin

from .models import CitySearchHistory, PlayerState, PlayerUpgrade, WeatherSnapshot, WeatherTask


@admin.register(PlayerState)
class PlayerStateAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "current_floor",
        "coins",
        "total_floors_travelled",
        "last_weather_city",
        "updated_at",
    )
    search_fields = ("user__username", "user__email", "last_weather_city")
    list_select_related = ("user",)
    ordering = ("-updated_at",)


@admin.register(PlayerUpgrade)
class PlayerUpgradeAdmin(admin.ModelAdmin):
    list_display = ("user", "upgrade_key", "level", "updated_at")
    search_fields = ("user__username", "user__email", "upgrade_key")
    list_filter = ("upgrade_key",)
    list_select_related = ("user",)
    raw_id_fields = ("user",)
    ordering = ("-updated_at",)


@admin.register(WeatherSnapshot)
class WeatherSnapshotAdmin(admin.ModelAdmin):
    list_display = ("city", "fetched_at")
    search_fields = ("city",)
    ordering = ("-fetched_at",)


@admin.register(CitySearchHistory)
class CitySearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "searched_at")
    search_fields = ("user__username", "user__email", "city")
    list_filter = ("city",)
    list_select_related = ("user",)
    raw_id_fields = ("user",)
    ordering = ("-searched_at",)


@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "title", "status", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "city", "title")
    list_filter = ("status", "city")
    list_select_related = ("user",)
    raw_id_fields = ("user",)
    ordering = ("-updated_at",)
