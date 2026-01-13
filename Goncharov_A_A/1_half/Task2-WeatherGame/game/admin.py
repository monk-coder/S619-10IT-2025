from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CitySearchHistory, PlayerState, PlayerUpgrade, WeatherSnapshot, WeatherTask


User = get_user_model()


class PlayerStateInline(admin.StackedInline):
    model = PlayerState
    can_delete = False
    extra = 1
    fk_name = "user"
    max_num = 1


class PlayerUpgradeInline(admin.TabularInline):
    model = PlayerUpgrade
    extra = 1
    fk_name = "user"


class WeatherTaskInline(admin.TabularInline):
    model = WeatherTask
    extra = 1
    fk_name = "user"


class CitySearchHistoryInline(admin.TabularInline):
    model = CitySearchHistory
    extra = 1
    fk_name = "user"


try:
    admin.site.unregister(User)
except NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [
        PlayerStateInline,
        PlayerUpgradeInline,
        WeatherTaskInline,
        CitySearchHistoryInline,
    ]


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
    autocomplete_fields = ("user",)
    ordering = ("-updated_at",)


@admin.register(PlayerUpgrade)
class PlayerUpgradeAdmin(admin.ModelAdmin):
    list_display = ("user", "upgrade_key", "level", "updated_at")
    search_fields = ("user__username", "user__email", "upgrade_key")
    list_filter = ("upgrade_key",)
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
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
    autocomplete_fields = ("user",)
    ordering = ("-searched_at",)


@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "title", "status", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "city", "title")
    list_filter = ("status", "city")
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    ordering = ("-updated_at",)
