# Практическая LLM на PyTorch Запуск
# Обучение
python train.py --batch_size=64 --lr=6e-4 --max_iters=5000 --eval_interval=500 --device=cuda

# Генерация
python sample.py --checkpoint=checkpoints/best.pt --prompt "ROMEO:" --max_new_tokens=200 --temperature=0.8 --top_k=50