# Production-Ready LLM Training Pipeline

## Быстрый запуск

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Обучение модели
python train.py --batch_size=64 --lr=6e-4 --max_iters=5000 --device=cuda

# 3. Генерация текста
python sample.py --checkpoint=checkpoints/best_model.pt --prompt="ROMEO:" --temperature=0.8 --top_k=50