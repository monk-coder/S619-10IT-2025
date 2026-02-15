.PHONY: help install train evaluate clean test

help:
	@echo "Доступные команды:"
	@echo "  install     - установка зависимостей"
	@echo "  train       - обучение токенизатора"
	@echo "  evaluate    - оценка токенизаторов"
	@echo "  clean       - очистка временных файлов"
	@echo "  test        - запуск тестов"

install:
	pip install -r requirements/dev.txt

train:
	python scripts/train.py --data data/raw/data.txt --merges 2000 8000

evaluate:
	python scripts/evaluate.py --models models/bpe_tokenizer_*.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

test:
	pytest tests/ -v --cov=src