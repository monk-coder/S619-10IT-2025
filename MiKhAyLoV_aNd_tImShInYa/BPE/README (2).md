# BPE Tokenizer

Реализация субсловного токенизатора на основе Byte Pair Encoding (BPE) с нуля.

## Описание проекта

Проект реализует полный пайплайн для BPE токенизации:
- Обучение токенизатора на текстовом корпусе
- Кодирование текста в последовательность ID токенов
- Декодирование последовательности ID обратно в текст
- Сохранение и загрузка обученного токенизатора
- Анализ метрик и эксперименты с разным количеством слияний


## Требования к окружению

- Python 3.7 или выше
- Библиотеки: numpy, tqdm, regex, matplotlib

## Установка и запуск

### 1. Клонирование репозитория


git clone https://github.com/smash6767/BPE
cd BPE

### 2. Установка зависимостей

pip install -r requirements.txt



Пример: Базовое использование
python
from bpe_tokenizer import BPETokenizer

# Загрузка обученного токенизатора
tokenizer = BPETokenizer()
tokenizer.load("bpe_tokenizer.json")  # файл создаётся после обучения

# Кодирование текста
text = "Hello, world!"
encoded = tokenizer.encode(text)
print(f"Encoded: {encoded}")
# Вывод: Encoded: [45, 12, 33, 33, 78, 23, 56, 89, 12, 34, 67]

# Декодирование обратно в текст
decoded = tokenizer.decode(encoded)
print(f"Decoded: {decoded}")
# Вывод: Decoded: Helloworld!