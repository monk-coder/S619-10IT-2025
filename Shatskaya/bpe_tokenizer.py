import json
import re
from collections import defaultdict, Counter
import pickle
import os
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt


class BPETokenizer:
    def init(self):
        self.vocab: Dict[str, int] = {}      # token -> id
        self.merges: Dict[Tuple[int, int], int] = {}  # (id1, id2) -> new_id
        self.id_to_token: Dict[int, str] = {}
        self.special_tokens = ["<|endoftext|>", "<|unk|>"]  # можно расширить

    def _get_stats(self, ids_list: List[List[int]]) -> Dict[Tuple[int, int], int]:
        """Подсчёт частоты пар соседних токенов"""
        counts = defaultdict(int)
        for ids in ids_list:
            for i in range(len(ids) - 1):
                counts[(ids[i], ids[i + 1])] += 1
        return counts

    def train(self, corpus: List[str], num_merges: int = 1000, verbose: bool = True):
        """Обучение BPE"""
        print(f"Начало обучения BPE. Корпус: {len(corpus)} документов, merges={num_merges}")

        # 1. Инициализация словаря байтами + специальные токены
        byte_tokens = [chr(i) for i in range(256)]
        all_tokens = byte_tokens + self.special_tokens
        for i, token in enumerate(all_tokens):
            self.vocab[token] = i
            self.id_to_token[i] = token

        current_id = len(self.vocab)

        # 2. Преобразуем текст в последовательности id (начально — байты)
        def text_to_ids(text: str) -> List[int]:
            return [ord(c) if ord(c) < 256 else ord(c) % 256 for c in text]  # упрощённо

        ids_list = [text_to_ids(text) for text in corpus]

        for merge_idx in tqdm(range(num_merges), disable=not verbose):
            stats = self._get_stats(ids_list)
            if not stats:
                break

            # Самая частая пара
            most_freq = max(stats.items(), key=lambda x: x[1])
            pair, freq = most_freq

            # Создаём новый токен
            new_token = self.id_to_token[pair[0]] + self.id_to_token[pair[1]]
            self.vocab[new_token] = current_id
            self.id_to_token[current_id] = new_token
            self.merges[pair] = current_id

            # Заменяем все вхождения пары
            new_ids_list = []
            for ids in ids_list:
                i = 0
                new_ids = []
                while i < len(ids):
                    if i < len(ids) - 1 and (ids[i], ids[i + 1]) == pair:
                        new_ids.append(current_id)
                        i += 2
                    else:
                        new_ids.append(ids[i])
                        i += 1
                new_ids_list.append(new_ids)
            ids_list = new_ids_list
            current_id += 1

        print(f"Обучение завершено. Размер словаря: {len(self.vocab)}")

    def encode(self, text: str) -> List[int]:
        """Кодирование текста"""
        if not self.merges:
            # fallback — байты
            return [ord(c) if ord(c) < 256 else 0 for c in text]

        ids = [ord(c) if ord(c) < 256 else 0 for c in text]

        # Применяем merges в порядке обучения (жадно)
        while len(ids) >= 2:
            stats = self._get_stats([ids])
            if not stats:
                break

            # Находим пару с самым ранним merge
            best_pair = None
            best_rank = float('inf')
            for pair in stats:
                if pair in self.merges:
                    rank = self.merges[pair]
                    if rank < best_rank:
                        best_rank = rank
                        best_pair = pair

            if best_pair is None:
                break

            # Сливаем
            new_ids = []
            i = 0
            while i < len(ids):
                if i < len(ids) - 1 and (ids[i], ids[i + 1]) == best_pair:
                    new_ids.append(self.merges[best_pair])
                    i += 2
                else:
                    new_ids.append(ids[i])
                    i += 1
            ids = new_ids

        return ids
def decode(self, ids: List[int]) -> str:
        """Декодирование"""
        tokens = [self.id_to_token.get(i, "<|unk|>") for i in ids]
        text = ''.join(tokens)
        return text

    def save(self, path: str = "bpe_model.pkl"):
        """Сохранение модели"""
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'vocab': self.vocab,
                'merges': dict(self.merges),  # tuple -> int
                'id_to_token': self.id_to_token
            }, f)
        print(f"Модель сохранена в {path}")

    def load(self, path: str = "bpe_model.pkl"):
        """Загрузка модели"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.vocab = data['vocab']
        self.merges = {tuple(k) if isinstance(k, list) else k: v for k, v in data['merges'].items()}
        self.id_to_token = data['id_to_token']
        print(f"Модель загружена из {path}. Словарь: {len(self.vocab)} токенов")


# ====================== Вспомогательные функции ======================

def load_corpus(file_path: str = "data.txt") -> List[str]:
    """Загрузка корпуса"""
    with open(file_path, encoding='utf-8') as f:
        text = f.read()
    # Простое разбиение на предложения/абзацы
    documents = [doc.strip() for doc in re.split(r'\n{2,}', text) if doc.strip()]
    return documents


def split_train_val(documents: List[str], val_ratio: float = 0.1):
    split = int(len(documents) * (1 - val_ratio))
    return documents[:split], documents[split:]


def analyze_tokenizer(tokenizer: BPETokenizer, val_texts: List[str]):
    """Анализ метрик"""
    lengths = []
    for text in tqdm(val_texts, desc="Анализ валидации"):
        ids = tokenizer.encode(text)
        lengths.append(len(ids))

    lengths = np.array(lengths)
    print("\n=== Метрики токенизатора ===")
    print(f"Размер словаря: {len(tokenizer.vocab)}")
    print(f"Средняя длина в токенах: {lengths.mean():.2f}")
    print(f"Медианная длина: {np.median(lengths):.2f}")
    print(f"90-й перцентиль: {np.percentile(lengths, 90):.2f}")
    print(f"Макс длина: {lengths.max()}")

    # Гистограмма
    plt.figure(figsize=(10, 6))
    plt.hist(lengths, bins=50)
    plt.title("Распределение длины последовательностей в токенах")
    plt.xlabel("Количество токенов")
    plt.ylabel("Частота")
    plt.savefig("token_length_dist.png")
    plt.show()