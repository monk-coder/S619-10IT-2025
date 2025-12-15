import sys
print("Python версия:", sys.version)
print("🌍 Запускаю сервер...")

try:
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    
    PORT = 8000
    
    print(f"📍 Сервер запущен: http://localhost:{PORT}")
    print("📁 Открой этот адрес в браузере")
    print("⏹️  Для остановки нажми Ctrl+C")
    print("-" * 50)
    
    server = HTTPServer(('localhost', PORT), SimpleHTTPRequestHandler)
    server.serve_forever()
    
except Exception as e:
    print(f"💥 Ошибка: {e}")
    print("Возможно, проблема с Python")
    input("Нажми Enter для выхода...")