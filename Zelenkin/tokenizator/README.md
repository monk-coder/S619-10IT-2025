BPE токенизатор
Реализация субсловного токенизатора на основе Byte Pair Encoding (BPE) с нуля. Проект включает полный пайплайн: обучение токенизатора, кодирование и декодирование текста.

📋 Описание
Byte Pair Encoding (BPE) - это алгоритм субсловной токенизации, который используется в современных NLP моделях (GPT, BERT, LLaMA и др.). Алгоритм начинает с базовых символов и итеративно объединяет наиболее частотные пары токенов, создавая словарь субсловных единиц.

🚀 Установка
Требования
Python 3.11+

pip (менеджер пакетов)

Шаги по установке
Клонируйте репозиторий

bash
git clone <url-вашего-репозитория>
cd BPE
Создайте виртуальное окружение (рекомендуется)

bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
Установите зависимости

bash
pip install -r requirements.txt
📁 Структура проекта
text
BPE/
├── src/                    # Исходный код
│   ├── tokenizer/          # Модуль токенизатора
│   │   ├── base.py         # Базовые классы
│   │   ├── bpe_core.py     # Ядро BPE алгоритма
│   │   └── tokenizer.py    # Основной класс токенизатора
│   ├── utils/               # Утилиты
│   │   ├── data_loader.py   # Загрузка данных
│   │   ├── vocabulary.py    # Работа со словарем
│   │   └── metrics.py       # Метрики и статистика
│   └── visualization/       # Визуализация
│       └── plots.py         # Построение графиков
├── scripts/                 # Исполняемые скрипты
│   ├── train.py             # Обучение токенизатора
│   └── evaluate.py          # Оценка и анализ
├── data/                    # Данные
│   └── raw/                 # Исходные данные
│       └── data.txt         # Входной корпус (UTF-8)
├── models/                   # Сохраненные модели
├── results/                  # Результаты экспериментов
├── requirements.txt          # Зависимости
└── README.md                 # Документация
💻 Использование
1. Подготовка данных
Поместите ваш текстовый корпус в файл data/raw/data.txt (формат UTF-8). Каждая строка - отдельный документ/предложение.

Пример содержимого data.txt:

text
Это первый пример текста для обучения токенизатора.
BPE алгоритм используется в современных NLP моделях.
Сегодня хорошая погода для программирования на Python.
2. Обучение токенизатора
Запустите скрипт обучения:

bash
# Базовый запуск
python scripts/train.py --data data/raw/data.txt --merges 2000 8000

# С дополнительными параметрами
python scripts/train.py --data data/raw/data.txt --merges 1000 5000 10000 --val-size 0.15 --lowercase
Параметры:

--data - путь к файлу с данными

--merges - количество слияний (можно указать несколько значений)

--output-dir - директория для сохранения моделей (по умолчанию: models)

--val-size - размер валидационной выборки (по умолчанию: 0.1)

--lowercase - приводить текст к нижнему регистру

3. Оценка и анализ
После обучения проанализируйте результаты:

bash
python scripts/evaluate.py --models models/bpe_tokenizer_*.json --data data/raw/data.txt
Результаты сохраняются в папку results/:

length_distribution.png - распределение длин токенизации

metrics_comparison.png - сравнение метрик

evaluation_results.json - численные результаты

4. Использование токенизатора в коде
python
from src.tokenizer import BPETokenizer

# Загрузка обученного токенизатора
tokenizer = BPETokenizer()
tokenizer.load('models/bpe_tokenizer_8000.json')

# Кодирование текста
text = "Hello, world! This is a test."
token_ids = tokenizer.encode(text)
print(f"Токены: {token_ids}")
print(f"Количество токенов: {len(token_ids)}")

# Декодирование обратно
decoded = tokenizer.decode(token_ids)
print(f"Декодировано: {decoded}")
print(f"Совпадает с оригиналом: {decoded == text.lower()}")

# Получение статистики
from src.utils.metrics import TokenizerMetrics
metrics = TokenizerMetrics(tokenizer)
stats = metrics.get_statistics([text])
print(f"Статистика: {stats}")
📊 Результаты и метрики
При запуске с разным количеством слияний вы получите:

Количество слияний	Размер словаря	Средняя длина	95-й перцентиль
0 (только символы)	~100	высокая	-
2000	~2100	средняя	-
8000	~8100	низкая	-
Метрики включают:
Размер словаря

Среднюю длину последовательности токенов

Медианную длину

Стандартное отклонение

Минимальную и максимальную длину

95-й и 99-й перцентили

Общее количество токенов

🧪 Тестирование
Для проверки корректности работы:

python
# Проверка обратимости (decode(encode(x)) == x)
test_text = "Проверка обратимости кодирования."
encoded = tokenizer.encode(test_text)
decoded = tokenizer.decode(encoded)
assert decoded == test_text.lower(), "Ошибка обратимости!"
🔧 Возможные проблемы и решения
Файл data.txt не найден
bash
# Создайте папку и файл вручную
mkdir data\raw
# Добавьте текст в data\raw\data.txt
Ошибки кодировки
Убедитесь, что файл сохранен в UTF-8:

bash
# В PowerShell создайте файл с правильной кодировкой
"Ваш текст" | Out-File -FilePath data\raw\data.txt -Encoding UTF8
Ошибки импорта
bash
# Убедитесь, что все зависимости установлены
pip install -r requirements.txt
📈 Примеры
Пример 1: Обучение на маленьком корпусе
bash
python scripts/train.py --data data/raw/data.txt --merges 100 500
Пример 2: Сравнение трех конфигураций
bash
python scripts/train.py --data data/raw/data.txt --merges 0 2000 8000
python scripts/evaluate.py --models models/bpe_tokenizer_*.json
Пример 3: Анализ длинных токенизаций
python
from src.utils.metrics import TokenizerMetrics

metrics = TokenizerMetrics(tokenizer)
long_texts = metrics.find_long_tokenizations(val_data, top_k=5)
for text, length in long_texts:
    print(f"Длина: {length}, Текст: {text[:50]}...")
📚 Теоретическая справка
Byte Pair Encoding (BPE):

Начинается с базового словаря символов

Подсчитывает частоты всех пар соседних символов

Объединяет самую частую пару в новый токен

Повторяет шаги 2-3 заданное количество раз

Преимущества BPE:

Решает проблему OOV (out-of-vocabulary) слов

Компромисс между символьным и словесным уровнями

Эффективен для морфологически богатых языков

🤝 Вклад в проект
Форкните репозиторий

Создайте ветку для новой функциональности

Зафиксируйте изменения

Отправьте пулл-реквест

📄 Лицензия
MIT License

📧 Контакты
По вопросам и предложениям: [ваш email]