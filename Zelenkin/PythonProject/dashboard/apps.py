from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = 'Погодный Дашборд'

    def ready(self):
        # Импорт сигналов (если будут добавлены позже)
        try:
            from . import signals
        except ImportError:
            pass