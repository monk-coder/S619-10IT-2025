# tokenizer.py
import re
from collections import defaultdict

class BPETokenizer:
    def __init__(self, vocab_size=5000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.merges = {}
        self.token_to_id = {}
        self.id_to_token = {}
        
    def preprocess(self, text):
        """Разбиваем текст на базовые символы"""
        text = re.sub(r'([^\s\w])', r' \1 ', text).lower()
        return text.split()
    
    def get_stats(self, vocab):
        """Считаем частоты пар символов"""
        pairs = defaultdict(int)
        for word, freq in vocab.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i+1])] += freq
        return pairs
    
    def merge_vocab(self, pair, vocab):
        """Объединяем самую частую пару"""
        bigram = re.escape(pair[0]) + r'\s+' + re.escape(pair[1])
        p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
        new_vocab = {}
        for word in vocab:
            new_word = p.sub(pair[0] + pair[1], word)
            new_vocab[new_word] = vocab[word]
        return new_vocab
    
    def train(self, text):
        """Обучение BPE токенизатора"""
        # Инициализация: каждый символ — отдельный токен
        tokens = self.preprocess(text)
        vocab = defaultdict(int)
        for token in tokens:
            vocab[' '.join(token)] += 1
        
        # Базовый словарь символов
        self.vocab = set(c for token in tokens for c in token)
        
        # Итеративное слияние
        for _ in range(self.vocab_size - len(self.vocab)):
            pairs = self.get_stats(vocab)
            if not pairs:
                break
            best = max(pairs, key=pairs.get)
            self.merges[best] = len(self.merges)
            self.vocab.add(best[0] + best[1])
            vocab = self.merge_vocab(best, vocab)
        
        # Финализация словаря
        self._build_token_maps()
    
    def _build_token_maps(self):
        """Создаем отображения token↔id"""
        # Спец-токены
        special = ['<pad>', '<unk>', '<s>', '</s>']
        for tok in special:
            self.vocab.add(tok)
        
        for idx, token in enumerate(sorted(self.vocab)):
            self.token_to_id[token] = idx
            self.id_to_token[idx] = token
        
        self.unk_id = self.token_to_id['<unk>']
    
    def encode(self, text, max_length=None):
        """Токенизация текста в последовательность ID"""
        tokens = self.preprocess(text)
        ids = []
        for token in tokens:
            word = ' '.join(token)
            # Жадное применение слияний
            while len(word.split()) > 1:
                symbols = word.split()
                pairs = [(symbols[i], symbols[i+1]) for i in range(len(symbols)-1)]
                merged = False
                for pair in pairs:
                    if pair in self.merges:
                        word = re.sub(
                            re.escape(pair[0]) + r'\s+' + re.escape(pair[1]),
                            pair[0] + pair[1],
                            word,
                            count=1
                        )
                        merged = True
                        break
                if not merged:
                    break
            # Конвертация в ID
            for sym in word.split():
                ids.append(self.token_to_id.get(sym, self.unk_id))
        
        if max_length:
            ids = ids[:max_length]
        return ids
    
    def decode(self, ids):
        """Декодирование ID обратно в текст"""
        tokens = [self.id_to_token.get(i, '<unk>') for i in ids]
        return ''.join(tokens).replace('</s>', '').strip()
    
    @property
    def vocab_len(self):
        return len(self.token_to_id)