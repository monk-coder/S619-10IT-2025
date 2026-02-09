import json
import unicodedata
from collections import defaultdict
import random
import math
from typing import List, Dict, Tuple, Optional


class BPETokenizer:
    def __init__(self):
        self.vocab = {}
        self.id_to_token = {}
        self.merges = []
        self.special_tokens = {"<unk>": 0, "<pad>": 1, "<s>": 2, "</s>": 3}
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True):
        # Подсчет частот
        vocab = defaultdict(int)
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            words = text.split()
            for word in words:
                if word:
                    vocab[" ".join(list(word))] += 1
        
        # Инициализация словаря символов
        chars = set()
        for word in vocab.keys():
            chars.update(word.split())
        
        # Создание базового словаря
        self.vocab = {char: i + 4 for i, char in enumerate(sorted(chars))}
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        # Выполнение слияний
        for _ in range(num_merges):
            # Подсчет пар
            pairs = defaultdict(int)
            for word, freq in vocab.items():
                symbols = word.split()
                for i in range(len(symbols) - 1):
                    pairs[(symbols[i], symbols[i + 1])] += freq
            
            if not pairs:
                break
            
            # Наиболее частая пара
            best_pair = max(pairs.items(), key=lambda x: (x[1], x[0]))[0]
            
            if pairs[best_pair] < 2:
                break
            
            # Сохранение правила
            self.merges.append(best_pair)
            
            # Обновление словаря
            new_vocab = {}
            bigram = " ".join(best_pair)
            replacement = "".join(best_pair)
            for word, freq in vocab.items():
                new_vocab[word.replace(bigram, replacement)] = freq
            vocab = new_vocab
            
            # Добавление нового токена
            new_token = "".join(best_pair)
            if new_token not in self.vocab:
                new_id = len(self.vocab)
                self.vocab[new_token] = new_id
                self.id_to_token[new_id] = new_token
    
    def encode(self, text: str) -> List[int]:
        text = unicodedata.normalize('NFKC', text)
        words = text.split()
        ids = []
        
        for word in words:
            tokens = list(word)
            
            # Применение правил слияния
            for pair in self.merges:
                new_tokens = []
                i = 0
                while i < len(tokens):
                    if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                        new_tokens.append(pair[0] + pair[1])
                        i += 2
                    else:
                        new_tokens.append(tokens[i])
                        i += 1
                
                if len(new_tokens) < len(tokens):
                    tokens = new_tokens
            
            # Конвертация в ID
            for token in tokens:
                if token in self.vocab:
                    ids.append(self.vocab[token])
                else:
                    for char in token:
                        if char in self.vocab:
                            ids.append(self.vocab[char])
                        else:
                            ids.append(0)  # <unk>
        
        return ids
    
    def decode(self, ids: List[int]) -> str:
        tokens = []
        for token_id in ids:
            if token_id in self.id_to_token:
                tokens.append(self.id_to_token[token_id])
            else:
                tokens.append("<unk>")
        
        return "".join(tokens)
    
    def save(self, filepath: str):
        data = {
            'vocab': self.vocab,
            'merges': [list(pair) for pair in self.merges]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.vocab = {k: int(v) for k, v in data['vocab'].items()}
        self.merges = [tuple(pair) for pair in data['merges']]
        self.id_to_token = {v: k for k, v in self.vocab.items()}
