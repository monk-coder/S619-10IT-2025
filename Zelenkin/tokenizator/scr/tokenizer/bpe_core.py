"""Ядро BPE алгоритма - низкоуровневые операции."""

from collections import defaultdict
from typing import List, Dict, Tuple, Set


class BPECore:
    """
    Ядро BPE алгоритма.
    Содержит только основные операции без логики токенизатора.
    """
    
    def __init__(self):
        self.merges: List[Tuple[str, str]] = []
        self.vocab: Set[str] = set()
        
    @staticmethod
    def get_initial_vocab(word_counts: Dict[str, int]) -> Set[str]:
        """Получение начального словаря символов."""
        chars = {' '}  # пробел нужен всегда
        
        if word_counts:
            for word in word_counts:
                chars.update(word.split())
        
        return chars
        
    @staticmethod
    def get_stats(word_counts: Dict[str, int]) -> Dict[Tuple[str, str], int]:
        """
        Подсчет частот пар символов.
        
        Time complexity: O(V * L) где V - количество слов, L - средняя длина
        Memory complexity: O(P) где P - количество уникальных пар
        """
        pairs = defaultdict(int)
        for word, freq in word_counts.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs
    
    @staticmethod
    def merge_vocab(pair: Tuple[str, str], word_counts: Dict[str, int]) -> Dict[str, int]:
        """
        Применение слияния пары ко всем словам.
        
        Time complexity: O(V * L) где V - количество слов, L - средняя длина
        Memory complexity: O(V)
        """
        new_word_counts = {}
        bigram = ' '.join(pair)
        merged = ''.join(pair)
        
        for word, freq in word_counts.items():
            if bigram in word:
                new_word = word.replace(bigram, merged)
                new_word_counts[new_word] = new_word_counts.get(new_word, 0) + freq
            else:
                new_word_counts[word] = new_word_counts.get(word, 0) + freq
                
        return new_word_counts
    
    @staticmethod
    def tokenize_word(word: str, merges: List[Tuple[str, str]]) -> List[str]:
        """
        Токенизация слова с применением правил слияния.
        
        Time complexity: O(M * L) где M - количество слияний, L - длина слова
        Memory complexity: O(L)
        """
        if not word:
            return []
        
        tokens = list(word)
        
        for merge in merges:
            i = 0
            while i < len(tokens) - 1:
                if tokens[i] == merge[0] and tokens[i + 1] == merge[1]:
                    tokens = tokens[:i] + [merge[0] + merge[1]] + tokens[i + 2:]
                else:
                    i += 1
        return tokens
