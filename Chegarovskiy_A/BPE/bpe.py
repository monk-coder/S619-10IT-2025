"""
Byte Pair Encoding токенизатор.
"""

import json
import re
from collections import defaultdict
from typing import List, Tuple, Dict


class BPETokenizer:
    def __init__(self):
        self.vocab = {}
        self.inverse_vocab = {}
        self.merges = []
        self.word_end = '</w>'
    
    def _get_pairs(self, words):
        pairs = defaultdict(int)
        for word in words:
            for i in range(len(word) - 1):
                pairs[(word[i], word[i+1])] += 1
        return pairs
    
    def _merge_pair(self, words, pair, new_token):
        a, b = pair
        result = []
        for word in words:
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and word[i] == a and word[i+1] == b:
                    new_word.append(new_token)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            result.append(new_word)
        return result
    
    def _split_into_words(self, text):
        words = re.findall(r'\S+|\s+', text)
        result = []
        for w in words:
            if w.strip():
                result.append(list(w) + [self.word_end])
            else:
                result.append([w])
        return result
    
    def train(self, corpus, num_merges=2000):
        print("Подготовка данных...")
        all_chars = set()
        for text in corpus:
            all_chars.update(text)
        all_chars.add(self.word_end)
        
        self.vocab = {c: i for i, c in enumerate(sorted(all_chars))}
        self.inverse_vocab = {i: c for c, i in self.vocab.items()}
        
        words = []
        for text in corpus:
            words.extend(self._split_into_words(text))
        
        print(f"Слияний: 0/{num_merges}")
        for step in range(num_merges):
            pairs = self._get_pairs(words)
            if not pairs:
                break
            
            best_pair = max(pairs.items(), key=lambda x: x[1])[0]
            new_token = best_pair[0] + best_pair[1]
            
            if new_token not in self.vocab:
                self.vocab[new_token] = len(self.vocab)
                self.inverse_vocab[self.vocab[new_token]] = new_token
            
            self.merges.append(best_pair)
            words = self._merge_pair(words, best_pair, new_token)
            
            if (step + 1) % 500 == 0:
                print(f"Слияний: {step+1}/{num_merges}")
        
        print(f"Готово! Словарь: {len(self.vocab)} токенов")
        return self
    
    def encode(self, text):
        words = self._split_into_words(text)
        
        for a, b in self.merges:
            new_token = a + b
            words = self._merge_pair(words, (a, b), new_token)
        
        ids = []
        for word in words:
            for token in word:
                ids.append(self.vocab[token])
        return ids
    
    def decode(self, ids):
        tokens = [self.inverse_vocab[i] for i in ids]
        text = ''.join(tokens)
        return text.replace(self.word_end, ' ').strip()
    
    def save(self, path):
        data = {
            'vocab': self.vocab,
            'merges': self.merges,
            'word_end': self.word_end
        }
        with open(f'{path}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"Сохранено в {path}.json")
    
    def load(self, path):
        with open(f'{path}.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.vocab = data['vocab']
        self.merges = [tuple(m) for m in data['merges']]
        self.word_end = data['word_end']
        self.inverse_vocab = {int(i): c for c, i in self.vocab.items()}
        print(f"Загружено из {path}.json")
        return self
