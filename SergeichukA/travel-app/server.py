import http.server
import socketserver
import os

# Указываем порт
PORT = 8000

# Меняем директорию на текущую папку
web_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(web_dir)

# Создаем обработчик
Handler = http.server.SimpleHTTPRequestHandler

# Запускаем сервер
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Сервер запущен на http://localhost:{PORT}")
    print("Папка:", web_dir)
    print("Для остановки нажмите Ctrl+C")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")