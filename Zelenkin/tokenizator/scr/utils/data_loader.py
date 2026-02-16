"""Утилиты для загрузки и предобработки данных."""

from typing import List, Tuple, Union
from pathlib import Path
import unicodedata
import re
import os


class TextPreprocessor:
    """Предобработка текста."""

    def __init__(self, lowercase: bool = True, strip_accents: bool = False):
        self.lowercase = lowercase
        self.strip_accents = strip_accents
        self.whitespace_re = re.compile(r'\s+')

    def process(self, text: str) -> str:
        """Предобработка одного текста."""
        if self.lowercase:
            text = text.lower()
        if self.strip_accents:
            text = self._remove_accents(text)
        text = self.whitespace_re.sub(' ', text).strip()
        return text

    @staticmethod
    def _remove_accents(text: str) -> str:
        normalized = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in normalized if not unicodedata.combining(c)])


class DataLoader:
    """Загрузка и разбиение данных."""

    def __init__(self, data_path: Union[str, Path]):
        self.data_path = Path(data_path)
        print(f"Ищем файл: {self.data_path.absolute()}")

    def load_corpus(self) -> List[str]:
        """Загрузка корпуса из файла."""
        # Проверяем абсолютный путь
        abs_path = self.data_path.absolute()
        print(f"Абсолютный путь: {abs_path}")
        print(f"Файл существует: {abs_path.exists()}")

        if not abs_path.exists():
            # Создаем файл принудительно
            print("Файл не найден. СОЗДАЮ НОВЫЙ ФАЙЛ...")
            abs_path.parent.mkdir(parents=True, exist_ok=True)

            test_data = [
                "Это первый пример текста для обучения токенизатора.",
                "BPE алгоритм используется в современных NLP моделях.",
                "Сегодня хорошая погода для программирования на Python.",
                "Машинное обучение и обработка естественного языка.",
                "Токенизация важный этап в обработке текстов."
            ]

            with open(abs_path, 'w', encoding='utf-8') as f:
                for line in test_data:
                    f.write(line + '\n')
            print(f"Файл создан: {abs_path}")

        # Читаем файл
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            print(f"Загружено {len(lines)} строк")
            return lines
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return []

    @staticmethod
    def train_val_split(data: List[str], val_size: float = 0.1, seed: int = 42) -> Tuple[List[str], List[str]]:
        """Разбиение на обучающую и валидационную выборки."""
        import random
        random.seed(seed)

        indices = list(range(len(data)))
        random.shuffle(indices)

        split_point = int(len(data) * (1 - val_size))
        train_indices = indices[:split_point]
        val_indices = indices[split_point:]

        train_data = [data[i] for i in train_indices]
        val_data = [data[i] for i in val_indices]

        return train_data, val_data