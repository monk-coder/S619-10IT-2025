@echo off
REM Скрипт для быстрого запуска проекта Weather Dashboard на Windows

echo 🌤️  Запуск Weather Dashboard...

REM Проверяем наличие виртуального окружения
if not exist "venv" (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
)

REM Активируем виртуальное окружение
echo 🔧 Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo 📥 Установка зависимостей...
pip install -r requirements.txt

REM Проверяем наличие .env файла
if not exist ".env" (
    echo ⚙️  Создание файла .env...
    copy env_example.txt .env
    echo ⚠️  Не забудьте добавить ваш OpenWeatherMap API ключ в файл .env
)

REM Применяем миграции
echo 🗄️  Применение миграций...
python manage.py makemigrations
python manage.py migrate

REM Собираем статические файлы
echo 📁 Сбор статических файлов...
python manage.py collectstatic --noinput

REM Запускаем сервер
echo 🚀 Запуск сервера разработки...
echo 📱 Приложение будет доступно по адресу: http://127.0.0.1:8000/
python manage.py runserver

pause
