# debug_run.py
import sys, os
print("🔍 Запуск диагностики...", flush=True)

# 1. Проверка пути и файла
print(f"📂 Текущая папка: {os.getcwd()}", flush=True)
if os.path.exists("data.txt"):
    size = os.path.getsize("data.txt")
    print(f"✅ data.txt найден, размер: {size} байт", flush=True)
    if size == 0:
        print("⚠️ data.txt пустой! Положите в него текст.", flush=True)
        sys.exit(1)
else:
    print("❌ data.txt не найден в текущей папке!", flush=True)
    sys.exit(1)

# 2. Проверка импортов
try:
    import numpy, tqdm, matplotlib
    print("✅ Все библиотеки импортированы", flush=True)
except Exception as e:
    print(f"❌ Ошибка импорта: {e}", flush=True)
    sys.exit(1)

# 3. Запуск train.py с явным выводом
print("🚀 Запускаю train.py...", flush=True)
try:
    # Импортируем и запускаем main вручную, чтобы поймать любую ошибку
    from train import main
    main()
except Exception as e:
    import traceback
    print("\n🔴 СКРЫТАЯ ОШИБКА:", flush=True)
    print(traceback.format_exc(), flush=True)