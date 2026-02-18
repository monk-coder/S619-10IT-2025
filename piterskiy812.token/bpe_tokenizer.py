import json
import unicodedata
from collections import defaultdict
from typing import List, Dict, Tuple


class BPETokenizer:
    def __init__(self):
        self.vocab = {}
        self.id_to_token = {}
        self.merges = []
        self.special_tokens = {"<unk>": 0, "<pad>": 1}
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True):
        """Train BPE tokenizer on corpus."""
        
        # ШАГ 1: Собираем ВСЕ символы из корпуса
        all_chars = set()
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            for char in text:
                all_chars.add(char)
        
        # Добавляем спецтокены
        all_chars.add(' ')
        
        # Строим начальный словарь из символов
        char_list = sorted(list(all_chars))
        self.vocab = {}
        for i, char in enumerate(char_list):
            self.vocab[char] = i + 2  # +2 для <unk> и <pad>
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        if verbose:
            print(f"Initial vocab size: {len(self.vocab)}")
        
        # ШАГ 2: Подготавливаем данные для BPE
        # Разбиваем слова на символы с пробелами между ними
        word_freqs = defaultdict(int)
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            words = text.split()
            for word in words:
                if word:
                    # "hello" -> "h e l l o"
                    word_with_spaces = " ".join(list(word))
                    word_freqs[word_with_spaces] += 1
        
        if verbose:
            print(f"Unique words: {len(word_freqs)}")
        
        # ШАГ 3: BPE слияния
        for i in range(num_merges):
            # Считаем частоту пар
            pair_freqs = defaultdict(int)
            for word, freq in word_freqs.items():
                symbols = word.split()
                for j in range(len(symbols) - 1):
                    pair = (symbols[j], symbols[j + 1])
                    pair_freqs[pair] += freq
            
            if not pair_freqs:
                break
            
            # Находим самую частую пару
            best_pair = max(pair_freqs.items(), key=lambda x: x[1])[0]
            best_freq = pair_freqs[best_pair]
            
            if best_freq < 2:
                break
            
            # Добавляем пару в список слияний
            self.merges.append(best_pair)
            
            # Создаем новый токен из пары
            new_token = best_pair[0] + best_pair[1]
            
            # Добавляем новый токен в словарь
            if new_token not in self.vocab:
                new_id = len(self.vocab)
                self.vocab[new_token] = new_id
                self.id_to_token[new_id] = new_token
            
            # Обновляем частотный словарь - заменяем все вхождения пары
            new_word_freqs = defaultdict(int)
            bigram = " ".join(best_pair)
            replacement = new_token
            
            for word, freq in word_freqs.items():
                new_word = word.replace(bigram, replacement)
                new_word_freqs[new_word] += freq
            
            word_freqs = new_word_freqs
            
            if verbose and (i + 1) % 500 == 0:
                print(f"  Merge {i+1}/{num_merges}: '{best_pair[0]}+{best_pair[1]}' -> '{new_token}' (freq: {best_freq}), vocab: {len(self.vocab)}")
        
        if verbose:
            print(f"Final vocab size: {len(self.vocab)}")
            print(f"Merges performed: {len(self.merges)}")
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        text = unicodedata.normalize('NFKC', text)
        words = text.split()
        ids = []
        
        for i, word in enumerate(words):
            if i > 0:
                # Добавляем пробел между словами
                if " " in self.vocab:
                    ids.append(self.vocab[" "])
                else:
                    ids.append(1)  # <pad>
            
            # Токенизируем слово
            tokens = list(word)
            
            # Применяем все слияния
            for pair in self.merges:
                new_tokens = []
                j = 0
                while j < len(tokens):
                    if j < len(tokens) - 1 and tokens[j] == pair[0] and tokens[j + 1] == pair[1]:
                        new_tokens.append(pair[0] + pair[1])
                        j += 2
                    else:
                        new_tokens.append(tokens[j])
                        j += 1
                tokens = new_tokens
            
            # Конвертируем в ID
            for token in tokens:
                if token in self.vocab:
                    ids.append(self.vocab[token])
                else:
                    ids.append(0)  # <unk>
        
        return ids
    
    def decode(self, ids: List[int]) -> str:
        """Decode token IDs back to text."""
        tokens = []
        for token_id in ids:
            if token_id in self.id_to_token:
                tokens.append(self.id_to_token[token_id])
            else:
                tokens.append("<unk>")
        
        return "".join(tokens)
    
    def save(self, filepath: str):
        """Save tokenizer to file."""
        data = {
            'vocab': self.vocab,
            'merges': [list(pair) for pair in self.merges],
            'special_tokens': self.special_tokens
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved tokenizer to {filepath}")
    
    def load(self, filepath: str):
        """Load tokenizer from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vocab = {k: int(v) for k, v in data['vocab'].items()}
        self.merges = [tuple(pair) for pair in data['merges']]
        self.special_tokens = data['special_tokens']
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        print(f"Loaded tokenizer from {filepath}")
        print(f"Vocabulary size: {len(self.vocab)}")
