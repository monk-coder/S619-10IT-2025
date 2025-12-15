@echo off
chcp 65001
cls

echo ==================================
echo    🚀 ЗАПУСК СЕРВЕРА ПУТЕШЕСТВИЙ
echo ==================================
echo.

echo Проверяем Python...
py --version
if %errorlevel% neq 0 (
    echo.
    echo ❌ PYTHON НЕ НАЙДЕН!
    echo.
    echo 1. Скачай Python с python.org
    echo 2. Установи с галочкой "Add to PATH"
    echo.
    pause
    exit
)

echo.
echo ✅ Python работает!
echo Запускаем сервер...
echo.
echo 📍 Сайт: http://localhost:8000
echo 🌐 Нужен интернет для поиска стран
echo ⏹️  Остановка: Ctrl+C
echo ==================================
echo.

timeout /t 3
py server.py