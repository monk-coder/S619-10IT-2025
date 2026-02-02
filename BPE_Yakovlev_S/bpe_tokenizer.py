import json
from collections import defaultdict, Counter
from typing import List, Dict, Tuple


class BPETokenizer:
    def __init__(self):
        self.vocab = {}      # token -> id
        self.merges = []     # список пар [(a, b), ...] — ПОРЯДОК ВАЖЕН!
        self._inv_vocab = {} # id -> token
        self.val_lines = []  # для удобства

    def _get_stats(self, tokens: List[str]) -> Dict[Tuple[str, str], int]:
        """Считает частоты соседних пар."""
        pairs = defaultdict(int)
        for i in range(len(tokens) - 1):
            pairs[(tokens[i], tokens[i + 1])] += 1
        return pairs

    def _merge_pair(self, tokens: List[str], pair: Tuple[str, str], new_token: str) -> List[str]:
        """Заменяет все вхождения пары на новый токен."""
        i = 0
        new_tokens = []
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                new_tokens.append(new_token)
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        return new_tokens

    def train(self, file_path: str, num_merges: int = 1000, val_split: float = 0.1):
        # Загрузка всего корпуса
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip('\n') for line in f if line.strip()]
        
        if not lines:
            raise ValueError("Файл пустой!")
        
        # 🔥 ВАЖНО: собираем символы из ВСЕГО корпуса (чтобы покрыть и val тоже)
        all_chars = set()
        for line in lines:
            all_chars.update(line)
        
        # Делим на train/val ПОСЛЕ сбора символов
        split_idx = int(len(lines) * (1 - val_split))
        train_lines = lines[:split_idx]
        self.val_lines = lines[split_idx:]
        
        # Инициализация словаря символами
        self.vocab = {ch: i for i, ch in enumerate(sorted(all_chars))}
        next_id = len(self.vocab)
        
        # Представление слов как кортежей символов + частоты
        word_freqs = Counter()
        for line in train_lines:
            word_freqs[tuple(line)] += 1
        
        # BPE итерации
        for _ in range(num_merges):
            # Сбор статистики по парам
            stats = defaultdict(int)
            for word, freq in word_freqs.items():
                pairs = self._get_stats(list(word))
                for pair, count in pairs.items():
                    stats[pair] += count
            
            if not stats:
                break  # Больше нет пар для слияния
            
            # Выбираем самую частую пару
            best_pair = max(stats, key=stats.get)
            new_token = ''.join(best_pair)
            
            # Сохраняем пару в список (порядок = приоритет при кодировании)
            self.merges.append(best_pair)
            
            # Добавляем новый токен в словарь, если его ещё нет
            if new_token not in self.vocab:
                self.vocab[new_token] = next_id
                next_id += 1
            
            # Обновляем все слова: применяем слияние
            new_word_freqs = Counter()
            for word, freq in word_freqs.items():
                new_word = tuple(self._merge_pair(list(word), best_pair, new_token))
                new_word_freqs[new_word] += freq
            word_freqs = new_word_freqs
        
        # Инвертированный словарь для декодирования
        self._inv_vocab = {v: k for k, v in self.vocab.items()}

    def encode(self, text: str) -> List[int]:
        if not text:
            return []
        
        # Начинаем с символов
        tokens = list(text)
        
        # Применяем слияния в том же порядке, что и при обучении
        for pair in self.merges:
            new_token = ''.join(pair)
            # Применяем слияние только если оба элемента пары есть в текущих токенах
            if pair[0] in self.vocab and pair[1] in self.vocab:
                tokens = self._merge_pair(tokens, pair, new_token)
        
        # Преобразуем токены в ID
        ids = []
        for token in tokens:
            if token in self.vocab:
                ids.append(self.vocab[token])
            else:
                # На случай чего — разбиваем на символы (защита)
                for ch in token:
                    if ch in self.vocab:
                        ids.append(self.vocab[ch])
                    else:
                        raise ValueError(f"Символ '{ch}' не найден в словаре! Текст: '{text}'")
        return ids

    def decode(self, ids: List[int]) -> str:
        return ''.join(self._inv_vocab.get(i, '') for i in ids)

    def save(self, path: str):
        data = {
            "vocab": self.vocab,
            "merges": self.merges,
            "val_lines": self.val_lines
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str):
        obj = cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        obj.vocab = data["vocab"]
        obj.merges = [tuple(pair) for pair in data["merges"]]
        obj.val_lines = data.get("val_lines", [])
        obj._inv_vocab = {v: k for k, v in obj.vocab.items()}
        return obj
