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
        # Добавляем пробел в начальный словарь
        self.space_token = " "
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True):
        # Count word frequencies (сохраняем исходные строки с пробелами)
        vocab = defaultdict(int)
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            # Сохраняем как есть, чтобы потом разбить на слова и пробелы
            words = []
            current_word = []
            
            for char in text:
                if char == ' ':
                    if current_word:
                        words.append("".join(current_word))
                        current_word = []
                    words.append(" ")  # Пробел как отдельный "токен"
                else:
                    current_word.append(char)
            
            if current_word:
                words.append("".join(current_word))
            
            # Добавляем в словарь частот
            for word in words:
                if word:  # Не добавляем пустые строки
                    if word == " ":
                        # Пробелы просто считаем
                        vocab[" "] = vocab.get(" ", 0) + 1
                    else:
                        vocab[" ".join(list(word))] += 1
        
        # Initialize with characters (включая пробел)
        chars = set()
        for word in vocab.keys():
            if word == " ":
                chars.add(" ")
            else:
                chars.update(word.split())
        
        # Build initial vocab (гарантируем что пробел есть)
        char_list = sorted(chars)
        if " " not in char_list:
            char_list.insert(0, " ")  # Добавляем пробел первым
        
        self.vocab = {char: i + 2 for i, char in enumerate(char_list)}
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        if verbose:
            print(f"Vocab size: {len(self.vocab)} (includes space)")
        
        # BPE merges (только для не-пробельных символов)
        for _ in range(num_merges):
            # Count pairs (игнорируем пары с пробелами)
            pairs = defaultdict(int)
            for word, freq in vocab.items():
                if word == " ":  # Пропускаем пробелы
                    continue
                    
                symbols = word.split()
                for i in range(len(symbols) - 1):
                    pairs[(symbols[i], symbols[i + 1])] += freq
            
            if not pairs:
                break
            
            # Get best pair
            best_pair = max(pairs.items(), key=lambda x: x[1])[0]
            if pairs[best_pair] < 2:
                break
            
            # Save merge
            self.merges.append(best_pair)
            
            # Update vocab
            new_vocab = {}
            bigram = " ".join(best_pair)
            replacement = "".join(best_pair)
            
            for word, freq in vocab.items():
                if word == " ":  # Пробелы не меняем
                    new_vocab[word] = freq
                else:
                    new_vocab[word.replace(bigram, replacement)] = freq
            
            vocab = new_vocab
            
            # Add new token
            new_token = "".join(best_pair)
            if new_token not in self.vocab:
                new_id = len(self.vocab)
                self.vocab[new_token] = new_id
                self.id_to_token[new_id] = new_token
    
    def encode(self, text: str) -> List[int]:
        # Сохраняем исходный текст с пробелами
        text = unicodedata.normalize('NFKC', text)
        ids = []
        
        i = 0
        while i < len(text):
            if text[i] == ' ':
                # Пробел - добавляем его ID
                if " " in self.vocab:
                    ids.append(self.vocab[" "])
                else:
                    # Если пробела нет в словаре, добавляем
                    space_id = len(self.vocab)
                    self.vocab[" "] = space_id
                    self.id_to_token[space_id] = " "
                    ids.append(space_id)
                i += 1
            else:
                # Собираем слово
                start = i
                while i < len(text) and text[i] != ' ':
                    i += 1
                word = text[start:i]
                
                # Токенизируем слово с BPE
                tokens = list(word)
                
                # Apply merges
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
                    
                    if len(new_tokens) < len(tokens):
                        tokens = new_tokens
                
                # Add word tokens
                for token in tokens:
                    if token in self.vocab:
                        ids.append(self.vocab[token])
                    else:
                        ids.append(0)  # <unk>
        
        return ids
    
    def decode(self, ids: List[int]) -> str:
        tokens = []
        for token_id in ids:
            if token_id in self.id_to_token:
                token = self.id_to_token[token_id]
                tokens.append(token)
            else:
                tokens.append("<unk>")
        
        # Склеиваем все токены
        result = "".join(tokens)
        return result
    
    def save(self, filepath: str):
        data = {
            'vocab': self.vocab,
            'merges': self.merges
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.vocab = {k: int(v) for k, v in data['vocab'].items()}
        self.merges = [tuple(pair) for pair in data['merges']]
        self.id_to_token = {v: k for k, v in self.vocab.items()}
