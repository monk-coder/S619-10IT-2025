from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm, UserCreationForm as DjangoUserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import SearchHistory, WeatherSnapshot, WeatherTask


User = get_user_model()


class UserChangeForm(DjangoUserChangeForm):
    class Meta(DjangoUserChangeForm.Meta):
        model = User
        fields = ("username", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")


class UserCreationForm(DjangoUserCreationForm):
    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ("username",)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:  # pragma: no cover - defensive
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("id", "username", "is_active", "is_staff", "is_superuser", "last_login")
    list_filter = ("is_active", "is_staff", "is_superuser", "groups")
    search_fields = ("username", "=id")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "last_login", "date_joined")

    fieldsets = (
        (_("Account"), {"fields": ("id", "username", "password")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("city", "user", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("city", "user__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(WeatherTask)
class WeatherTaskAdmin(admin.ModelAdmin):
    list_display = ("city", "user", "short_text", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at", "user")
    search_fields = ("city", "text", "user__username")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    @admin.display(description=_("Text"))
    def short_text(self, obj):
        return obj.text[:60] + ("…" if len(obj.text) > 60 else "")


@admin.register(WeatherSnapshot)
class WeatherSnapshotAdmin(admin.ModelAdmin):
    list_display = ("city", "normalized_city", "fetched_at")
    search_fields = ("city", "normalized_city")
    readonly_fields = ("city", "normalized_city", "payload", "fetched_at")
    ordering = ("-fetched_at",)


admin.site.site_header = _("Weather Control Center")
admin.site.site_title = _("Weather Admin")
admin.site.index_title = _("Данные погодного сервиса")
