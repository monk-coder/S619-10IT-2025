# MiniGPT-from-scratch

Decoder-only Transformer на NumPy.

## Запуск

```bash
pip install -r requirements.txt

# Обучение
python train.py

# Генерация
python sample.py --prompt "The future of AI"
python sample.py --prompt "Once upon" --temperature 1.2 --top_k 40
