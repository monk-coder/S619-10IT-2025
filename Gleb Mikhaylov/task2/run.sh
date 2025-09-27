#!/bin/bash

# Скрипт для быстрого запуска проекта Weather Dashboard

echo "🌤️  Запуск Weather Dashboard..."

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Устанавливаем зависимости
echo "📥 Установка зависимостей..."
pip install -r requirements.txt

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "⚙️  Создание файла .env..."
    cp env_example.txt .env
    echo "⚠️  Не забудьте добавить ваш OpenWeatherMap API ключ в файл .env"
fi

# Применяем миграции
echo "🗄️  Применение миграций..."
python manage.py makemigrations
python manage.py migrate

# Собираем статические файлы
echo "📁 Сбор статических файлов..."
python manage.py collectstatic --noinput

# Запускаем сервер
echo "🚀 Запуск сервера разработки..."
echo "📱 Приложение будет доступно по адресу: http://127.0.0.1:8000/"
python manage.py runserver
