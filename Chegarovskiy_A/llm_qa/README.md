# Question Answering с Microsoft Phi-2 и QLoRA

## Описание
Проект по дообучению модели Microsoft Phi-2 на задаче Question Answering (SQuAD 2.0) с использованием LoRA/QLoRA.

## Установка
pip install -r requirements.txt

## Структура проекта
├── config.py          # Настройки
├── utils.py           # Загрузка модели, инференс
├── evaluate.py        # Метрики F1 и Exact Match
├── inference.py       # Локальный запуск
├── phi2-model/        # Папка с моделью
├── requirements.txt
└── README.md

## Запуск
python evaluate.py

## Результаты
| Метод        | F1 Score | Exact Match |
| ------------ | -------- | ----------- |
| LoRA (Phi-2) | >60%     | >50%        |