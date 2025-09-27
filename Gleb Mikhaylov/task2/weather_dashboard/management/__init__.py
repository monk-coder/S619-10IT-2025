from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from weather_dashboard.models import WeatherCache


class Command(BaseCommand):
    help = 'Очищает устаревший кэш погодных данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно очистить весь кэш',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=2,
            help='Количество часов для определения устаревших записей (по умолчанию: 2)',
        )

    def handle(self, *args, **options):
        force = options['force']
        hours = options['hours']
        
        if force:
            # Очищаем весь кэш
            count = WeatherCache.objects.count()
            WeatherCache.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Удалено {count} записей из кэша')
            )
        else:
            # Очищаем только устаревшие записи
            cutoff_time = timezone.now() - timedelta(hours=hours)
            expired_cache = WeatherCache.objects.filter(cached_at__lt=cutoff_time)
            count = expired_cache.count()
            expired_cache.delete()
            
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Удалено {count} устаревших записей из кэша')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Устаревших записей в кэше не найдено')
                )
        
        # Показываем текущее состояние кэша
        total_cache = WeatherCache.objects.count()
        self.stdout.write(f'Всего записей в кэше: {total_cache}')
