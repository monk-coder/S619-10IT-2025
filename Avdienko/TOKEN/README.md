# BPE Tokenizer Implementation

Полная реализация BPE (Byte Pair Encoding) токенизатора с нуля на Python.

## Особенности

- Обучение BPE с нуля на любом текстовом корпусе
- Эффективные алгоритмы подсчета частот пар
- Поддержка Unicode и специальных токенов
- Полная проверка: `decode(encode(text)) == text`
- Анализ метрик и визуализация

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd BPE