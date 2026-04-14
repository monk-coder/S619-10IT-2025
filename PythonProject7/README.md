# Parameter-Efficient Fine-Tuning for QA on SQuAD 2.0

## Описание
Fine-tuning Llama-3.2-1B на задаче Question Answering с использованием LoRA/QLoRA.

## Структура проекта
- `colab_training.ipynb` - обучение в Google Colab на T4 GPU
- `inference.py` - локальный запуск для тестирования
- `results/` - метрики и логи

## Быстрый старт

### Обучение (в Colab)
1. Открыть `colab_training.ipynb`
2. Runtime → Change runtime type → T4 GPU
3. Запустить все ячейки

### Локальный инференс
```bash
pip install -r requirements.txt
python inference.py