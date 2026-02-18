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
        # Сначала собираем ВСЕ символы из корпуса
        all_chars = set()
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            all_chars.update(text)  # Добавляем ВСЕ символы, включая пробелы
        
        # Добавляем специальные токены в набор символов
        all_chars.update([' '])  # Гарантируем наличие пробела
        
        # Строим начальный словарь из ВСЕХ символов
        char_list = sorted(all_chars)
        self.vocab = {char: i + 2 for i, char in enumerate(char_list)}
        self.vocab.update(self.special_tokens)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        if verbose:
            print(f"Initial vocab size: {len(self.vocab)} (all characters from corpus)")
        
        # Теперь считаем частоты для BPE
        word_freqs = defaultdict(int)
        for text in corpus:
            text = unicodedata.normalize('NFKC', text)
            words = text.split()
            for word in words:
                if word:
                    word_freqs[" ".join(list(word))] += 1
        
        if verbose:
            print(f"Word frequencies: {len(word_freqs)} unique words")
        
        # Perform BPE merges
        for _ in range(num_merges):
            # Count pairs
            pairs = defaultdict(int)
            for word, freq in word_freqs.items():
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
            new_word_freqs = {}
            bigram = " ".join(best_pair)
            replacement = "".join(best_pair)
            
            for word, freq in word_freqs.items():
                new_word_freqs[word.replace(bigram, replacement)] = freq
            
            word_freqs = new_word_freqs
            
            # Add new token
            new_token = "".join(best_pair)
            if new_token not in self.vocab:
                new_id = len(self.vocab)
                self.vocab[new_token] = new_id
                self.id_to_token[new_id] = new_token
        
        if verbose:
            print(f"Final vocab size: {len(self.vocab)}")
            print(f"Merges performed: {len(self.merges)}")
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        text = unicodedata.normalize('NFKC', text)
        ids = []
        
        i = 0
        while i < len(text):
            if text[i] == ' ':
                # Пробел - добавляем его ID
                if " " in self.vocab:
                    ids.append(self.vocab[" "])
                else:
                    ids.append(1)  # <pad> как запасной вариант
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
        """Decode token IDs back to text."""
        tokens = []
        for token_id in ids:
            if token_id in self.id_to_token:
                token = self.id_to_token[token_id]
                tokens.append(token)
            else:
                tokens.append("<unk>")
        
        # Просто склеиваем все токены
        return "".join(tokens)
    
    def save(self, filepath: str):
        """Save tokenizer to file."""
        data = {
            'vocab': self.vocab,
            'merges': self.merges,
            'special_tokens': self.special_tokens
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        """Load tokenizer from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vocab = {k: int(v) for k, v in data['vocab'].items()}
        self.merges = [tuple(pair) for pair in data['merges']]
        self.special_tokens = data['special_tokens']
        self.id_to_token = {v: k for k, v in self.vocab.items()}
