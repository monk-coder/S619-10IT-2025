import json
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
import numpy as np
from tqdm import tqdm


class BPETokenizer:
    """Класс для BPE токенизации."""
    
    def __init__(self):
        self.vocab = {}
        self.inverse_vocab = {}
        self.merges = {}
        self.special_tokens = {}
    
    def _get_stats(self, words: List[List[str]]) -> Dict[Tuple[str, str], int]:
        pairs = defaultdict(int)
        for word in words:
            for i in range(len(word) - 1):
                pair = (word[i], word[i + 1])
                pairs[pair] += 1
        return dict(pairs)
    
    def _merge_pair(self, words: List[List[str]], pair: Tuple[str, str], new_token: str) -> List[List[str]]:
        new_words = []
        for word in words:
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and word[i] == pair[0] and word[i + 1] == pair[1]:
                    new_word.append(new_token)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_words.append(new_word)
        return new_words
    
    def _preprocess_text(self, text: str) -> List[str]:
        text = re.sub(r'\s+', ' ', text.strip())
        return text.split()
    
    def _word_to_chars(self, word: str) -> List[str]:
        return list(word)
    
    def _init_vocab_from_corpus(self, all_words: List[str]) -> None:
        char_counts = Counter()
        for word in all_words:
            char_counts.update(self._word_to_chars(word))
        
        self.special_tokens = {
            '<unk>': 0,
            '<pad>': 1,
            '<s>': 2,
            '</s>': 3
        }
        
        self.vocab = {v: k for k, v in self.special_tokens.items()}
        next_id = len(self.special_tokens)
        
        for char in sorted(char_counts.keys()):
            self.vocab[next_id] = char
            next_id += 1
        
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
    
    def _perform_merges(self, words: List[List[str]], num_merges: int, verbose: bool) -> List[List[str]]:
        next_id = len(self.vocab)
        self.merges = {}
        
        iterator = tqdm(range(num_merges), desc="Слияние пар") if verbose else range(num_merges)
        
        for i in iterator:
            pairs = self._get_stats(words)
            if not pairs:
                if verbose:
                    print(f"Нет больше пар для слияния на шаге {i}")
                break
            
            most_frequent_pair = max(pairs.items(), key=lambda x: x[1])[0]
            new_token = ''.join(most_frequent_pair)
            
            self.merges[most_frequent_pair] = new_token
            self.vocab[next_id] = new_token
            self.inverse_vocab[new_token] = next_id
            next_id += 1
            
            words = self._merge_pair(words, most_frequent_pair, new_token)
            
            if verbose:
                iterator.set_description(f"Слияние: {most_frequent_pair[0]}+{most_frequent_pair[1]} -> {new_token}")
        
        return words
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True) -> 'BPETokenizer':
        """Обучение BPE токенизатора."""
        print("Сбор всех слов из корпуса...")
        all_words = []
        for text in corpus:
            all_words.extend(self._preprocess_text(text))
        
        self._init_vocab_from_corpus(all_words)
        
        print("Разбиение слов на символы...")
        words = [self._word_to_chars(word) for word in all_words]
        
        print(f"Начинаем слияние пар ({num_merges} итераций)...")
        self._perform_merges(words, num_merges, verbose)
        
        print(f"Обучение завершено! Размер словаря: {len(self.vocab)}")
        return self
    
    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        """Кодирование текста в ID токенов."""
        words = self._preprocess_text(text)
        encoded_tokens = []
        
        for word in words:
            tokens = self._word_to_chars(word)
            
            changed = True
            while changed:
                changed = False
                i = 0
                while i < len(tokens) - 1:
                    pair = (tokens[i], tokens[i + 1])
                    if pair in self.merges:
                        tokens = tokens[:i] + [self.merges[pair]] + tokens[i + 2:]
                        changed = True
                    else:
                        i += 1
            
            for token in tokens:
                if token in self.inverse_vocab:
                    encoded_tokens.append(self.inverse_vocab[token])
                else:
                    encoded_tokens.append(self.special_tokens['<unk>'])
        
        if add_special_tokens:
            return [self.special_tokens['<s>']] + encoded_tokens + [self.special_tokens['</s>']]
        
        return encoded_tokens
    
    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """Декодирование ID обратно в текст."""
        tokens = []
        special_ids = set(self.special_tokens.values())
        
        for token_id in ids:
            if skip_special_tokens and token_id in special_ids:
                continue
            
            if token_id in self.vocab:
                tokens.append(self.vocab[token_id])
            else:
                tokens.append('<unk>')
        
        return ''.join(tokens)
    
    def save(self, path: str) -> None:
        """Сохранение токенизатора в файл."""
        data = {
            'vocab': self.vocab,
            'merges': {f"{k[0]}||{k[1]}": v for k, v in self.merges.items()},
            'special_tokens': self.special_tokens
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Токенизатор сохранен в {path}")
    
    def load(self, path: str) -> 'BPETokenizer':
        """Загрузка токенизатора из файла."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vocab = {int(k): v for k, v in data['vocab'].items()}
        
        self.merges = {}
        for k, v in data['merges'].items():
            parts = k.split('||')
            self.merges[(parts[0], parts[1])] = v
        
        self.special_tokens = data['special_tokens']
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
        
        print(f"Токенизатор загружен из {path}")
        return self


def prepare_data(file_path: str, train_ratio: float = 0.9) -> Tuple[List[str], List[str]]:
    """Подготовка данных: разбиение на обучающую и проверочную выборки."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"Загружено {len(lines)} строк из файла")
    
    np.random.seed(42)
    indices = np.random.permutation(len(lines))
    
    split_idx = int(len(lines) * train_ratio)
    
    train_data = [lines[i] for i in indices[:split_idx]]
    val_data = [lines[i] for i in indices[split_idx:]]
    
    print(f"Обучающих примеров: {len(train_data)}")
    print(f"Проверочных примеров: {len(val_data)}")
    
    return train_data, val_data


def evaluate_tokenizer(tokenizer: BPETokenizer, val_data: List[str], sample_size: Optional[int] = None) -> Dict:
    """Оценка качества токенизатора."""
    print("Оценка токенизатора...")
    
    if sample_size and sample_size < len(val_data):
        val_sample = val_data[:sample_size]
    else:
        val_sample = val_data
    
    token_lengths = []
    
    for i, text in enumerate(val_sample):
        encoded = tokenizer.encode(text)
        token_lengths.append(len(encoded))
        
        if (i + 1) % 100 == 0:
            print(f"Обработано {i+1}/{len(val_sample)} примеров")
    
    metrics = {
        'vocab_size': len(tokenizer.vocab),
        'avg_token_length': np.mean(token_lengths),
        'std_token_length': np.std(token_lengths),
        'max_token_length': np.max(token_lengths),
        'min_token_length': np.min(token_lengths),
    }
    
    percentile_99 = np.percentile(token_lengths, 99)
    very_long_count = sum(1 for l in token_lengths if l > percentile_99)
    metrics['very_long_ratio'] = very_long_count / len(token_lengths) if token_lengths else 0
    
    return metrics


def experiment_different_merges(train_data: List[str], val_data: List[str], merge_values: List[int]) -> None:
    """Эксперимент с разным количеством слияний."""
    print("\n" + "="*60)
    print("ЭКСПЕРИМЕНТ: Сравнение разных значений num_merges")
    print("="*60)
    
    results = []
    
    for num_merges in merge_values:
        print(f"\n--- Обучение с num_merges = {num_merges} ---")
        
        tokenizer = BPETokenizer()
        tokenizer.train(train_data, num_merges=num_merges, verbose=True)
        
        metrics = evaluate_tokenizer(tokenizer, val_data[:50])
        results.append((num_merges, metrics))
        
        print(f"\nРезультаты для num_merges = {num_merges}:")
        print(f"  Размер словаря: {metrics['vocab_size']}")
        print(f"  Средняя длина: {metrics['avg_token_length']:.2f}")
        print(f"  Доля очень длинных: {metrics['very_long_ratio']:.2%}")
    
    print("\n" + "-"*60)
    print("СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print("-"*60)
    print(f"{'num_merges':<12} {'vocab_size':<12} {'avg_len':<10} {'very_long':<10}")
    print("-"*60)
    
    for num_merges, metrics in results:
        print(f"{num_merges:<12} {metrics['vocab_size']:<12} {metrics['avg_token_length']:<10.2f} {metrics['very_long_ratio']:<10.2%}")


def demonstrate_tokenizer(tokenizer: BPETokenizer, test_texts: List[str]) -> None:
    """Демонстрация работы encode/decode."""
    print("\n5. ДЕМОНСТРАЦИЯ ENCODE/DECODE")
    print("-" * 30)
    
    for text in test_texts:
        print(f"\nИсходный текст: {text}")
        encoded = tokenizer.encode(text)
        print(f"Закодировано: {encoded[:10]}{'...' if len(encoded) > 10 else ''} (всего {len(encoded)} токенов)")
        decoded = tokenizer.decode(encoded)
        print(f"Декодировано: {decoded}")


def print_metrics(metrics: Dict) -> None:
    """Вывод метрик оценки."""
    print(f"\nРезультаты оценки:")
    print(f"  Размер словаря: {metrics['vocab_size']}")
    print(f"  Средняя длина последовательности: {metrics['avg_token_length']:.2f}")
    print(f"  Стандартное отклонение: {metrics['std_token_length']:.2f}")
    print(f"  Макс длина: {metrics['max_token_length']}")
    print(f"  Мин длина: {metrics['min_token_length']}")
    print(f"  Доля очень длинных (топ 1%): {metrics['very_long_ratio']:.2%}")


def main():
    """Главная функция."""
    print("="*60)
    print("BPE ТОКЕНИЗАТОР - ДЕМОНСТРАЦИЯ РАБОТЫ")
    print("="*60)
    
    data_file = "data.txt"
    
    try:
        # Подготовка данных
        print("\n1. ПОДГОТОВКА ДАННЫХ")
        print("-" * 30)
        train_data, val_data = prepare_data(data_file)
        
        # Обучение токенизатора
        print("\n2. ОБУЧЕНИЕ ТОКЕНИЗАТОРА")
        print("-" * 30)
        tokenizer = BPETokenizer()
        tokenizer.train(train_data, num_merges=500, verbose=True)
        
        # Сохранение токенизатора
        print("\n3. СОХРАНЕНИЕ ТОКЕНИЗАТОРА")
        print("-" * 30)
        tokenizer.save("bpe_tokenizer.json")
        
        # Загрузка токенизатора
        print("\n4. ЗАГРУЗКА ТОКЕНИЗАТОРА")
        print("-" * 30)
        loaded_tokenizer = BPETokenizer()
        loaded_tokenizer.load("bpe_tokenizer.json")
        
        # Демонстрация encode/decode
        test_texts = [
            "Hello world!",
            "This is a test sentence.",
            "BPE tokenization is interesting.",
            "The quick brown fox jumps over the lazy dog."
        ]
        demonstrate_tokenizer(loaded_tokenizer, test_texts)
        
        # Оценка на валидационных данных
        print("\n6. ОЦЕНКА НА ВАЛИДАЦИОННЫХ ДАННЫХ")
        print("-" * 30)
        metrics = evaluate_tokenizer(loaded_tokenizer, val_data, sample_size=200)
        print_metrics(metrics)
        
        # Эксперимент с разными значениями num_merges
        print("\n7. ЭКСПЕРИМЕНТ С РАЗНЫМИ ЗНАЧЕНИЯМИ NUM_MERGES")
        print("-" * 30)
        experiment_different_merges(train_data[:500], val_data[:100], [0, 100, 500])
        
    except FileNotFoundError:
        print(f"\nОШИБКА: Файл '{data_file}' не найден!")
        print("Пожалуйста, создайте файл data.txt с текстом для обучения.")


if __name__ == "__main__":
    main()
