import json
import os
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

class BPETrainer:
    def __init__(self, vocab=None, merges=None):
        self.vocab = vocab if vocab is not None else []
        self.merges = merges if merges is not None else []
        self.token_to_id = {}
        if vocab:
            self.token_to_id = {token: i for i, token in enumerate(vocab)}

    def get_stats(self, tokens):
        """Подсчитывает частоту пар соседних токенов"""
        pairs = defaultdict(int)
        for i in range(len(tokens) - 1):
            pairs[(tokens[i], tokens[i + 1])] += 1
        return pairs

    def merge_tokens(self, tokens, pair):
        """Объединяет пару токенов в один"""
        new_tokens = []
        i = 0
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                new_tokens.append(pair[0] + pair[1])
                i += 2
            else:
                new_tokens.append(tokens[i])
                i += 1
        return new_tokens

    def train(self, corpus, num_merges):
        """Обучает BPE токенизатор на корпусе"""
        print(f"Начало обучения с {num_merges} слияниями...")
        
        # Начальная токенизация: каждый символ - отдельный токен
        tokenized_corpus = [list(text) for text in corpus]
        
        # Начальный словарь - все уникальные символы
        all_chars = set()
        for text in corpus:
            all_chars.update(text)
        vocab = sorted(list(all_chars))
        
        merges = []
        
        for i in range(num_merges):
            # Считаем статистику пар
            pair_freq = defaultdict(int)
            for tokens in tokenized_corpus:
                for j in range(len(tokens) - 1):
                    pair = (tokens[j], tokens[j + 1])
                    pair_freq[pair] += 1
            
            if not pair_freq:
                print(f"Прекращение обучения на шаге {i}: нет пар для слияния")
                break
            
            # Находим самую частую пару
            most_common_pair = max(pair_freq.items(), key=lambda x: x[1])[0]
            a, b = most_common_pair
            new_token = a + b
            
            # Выполняем слияние во всём корпусе
            for idx in range(len(tokenized_corpus)):
                tokenized_corpus[idx] = self.merge_tokens(tokenized_corpus[idx], most_common_pair)
            
            merges.append(most_common_pair)
            vocab.append(new_token)
            
            if (i + 1) % 1000 == 0:
                print(f"Выполнено {i + 1} слияний...")
        
        self.vocab = vocab
        self.merges = merges
        self.token_to_id = {token: i for i, token in enumerate(vocab)}
        
        print(f"Обучение завершено. Размер словаря: {len(vocab)}")

    def encode(self, text):
        """Кодирует текст в последовательность токенов"""
        if not text:
            return []
        
        tokens = list(text)
        
        # Применяем все правила слияния
        for a, b in self.merges:
            i = 0
            new_tokens = []
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == a and tokens[i + 1] == b:
                    new_tokens.append(a + b)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens
        
        # Преобразуем токены в индексы
        ids = []
        for token in tokens:
            if token in self.token_to_id:
                ids.append(self.token_to_id[token])
            else:
                # Если токен не найден, разбиваем на символы
                for char in token:
                    if char in self.token_to_id:
                        ids.append(self.token_to_id[char])
        
        return ids

    def decode(self, ids):
        """Декодирует последовательность токенов в текст"""
        tokens = []
        for id in ids:
            if id < len(self.vocab):
                tokens.append(self.vocab[id])
        return ''.join(tokens)

    def save(self, path):
        """Сохраняет токенизатор на диск"""
        os.makedirs(path, exist_ok=True)
        
        # Сохраняем словарь
        with open(os.path.join(path, 'vocab.txt'), 'w', encoding='utf-8') as f:
            for token in self.vocab:
                f.write(token + '\n')
        
        # Сохраняем правила слияния
        with open(os.path.join(path, 'merges.json'), 'w', encoding='utf-8') as f:
            json.dump(self.merges, f, ensure_ascii=False)
        
        print(f"Токенизатор сохранён в {path}")

    @classmethod
    def load(cls, path):
        """Загружает токенизатор с диска"""
        vocab_path = os.path.join(path, 'vocab.txt')
        merges_path = os.path.join(path, 'merges.json')
        
        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab = [line.rstrip('\n') for line in f]
        
        with open(merges_path, 'r', encoding='utf-8') as f:
            merges = json.load(f)
        
        return cls(vocab=vocab, merges=merges)

def load_data(file_path, val_ratio=0.1, output_dir='.'):
    """Загружает данные и разделяет на тренировочную и валидационную выборки"""
    print(f"Загрузка данных из {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    if not lines:
        raise ValueError(f"Файл {file_path} пустой!")
    
    val_size = max(1, int(len(lines) * val_ratio))
    val = lines[:val_size]
    train = lines[val_size:]
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, 'train.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(train))
    
    with open(os.path.join(output_dir, 'val.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(val))
    
    print(f"Данные разделены: {len(train)} тренировочных, {len(val)} валидационных")
    return train, val

def compute_metrics(trainer, val_corpus):
    """Вычисляет метрики токенизатора"""
    vocab_size = len(trainer.vocab)
    total_length = 0
    lengths = []
    
    for text in val_corpus:
        ids = trainer.encode(text)
        length = len(ids)
        total_length += length
        lengths.append(length)
    
    avg_length = total_length / len(val_corpus) if val_corpus else 0
    
    # Вычисляем 99-й процентиль
    lengths_sorted = sorted(lengths)
    threshold_idx = int(len(lengths_sorted) * 0.99)
    threshold = lengths_sorted[threshold_idx] if lengths_sorted else 0
    
    # Доля последовательностей длиннее порога
    share_long = sum(1 for l in lengths if l >= threshold) / len(lengths) if lengths else 0
    
    return vocab_size, avg_length, share_long

if __name__ == "__main__":
    try:
        # Загрузка данных
        train_corpus, val_corpus = load_data('data.txt', val_ratio=0.1, output_dir='.')
        
        # Параметры эксперимента
        num_merges_list = [0, 2000, 8000]
        results = []
        
        # Проводим эксперименты
        for num_merges in num_merges_list:
            print(f"\n{'='*60}")
            print(f"Эксперимент с {num_merges} слияниями")
            print(f"{'='*60}")
            
            trainer = BPETrainer()
            trainer.train(train_corpus, num_merges)
            
            vocab_size, avg_length, share_long = compute_metrics(trainer, val_corpus)
            
            print(f"Результаты:")
            print(f"  Размер словаря: {vocab_size}")
            print(f"  Средняя длина: {avg_length:.2f}")
            print(f"  Доля длинных: {share_long:.4f}")
            
            results.append((num_merges, vocab_size, avg_length, share_long))
            
            # Сохраняем токенизатор
            save_path = f'BPE_{num_merges}'
            trainer.save(save_path)
            
            # Тестируем на примере
            test_text = "Hello world!"
            encoded = trainer.encode(test_text)
            decoded = trainer.decode(encoded)
            print(f"  Тест: '{test_text}' -> {encoded} -> '{decoded}'")
        
        # Выводим итоговую таблицу
        print(f"\n{'='*60}")
        print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
        print(f"{'='*60}")
        print(f"{'Слияний':<15} {'Словарь':<15} {'Сред. длина':<15} {'Доля длинных':<15}")
        print(f"{'-'*60}")
        for num_merges, vocab_size, avg_length, share_long in results:
            print(f"{num_merges:<15} {vocab_size:<15} {avg_length:<15.2f} {share_long:<15.4f}")
        
        # Строим график
        num_merges_vals = [res[0] for res in results]
        avg_lengths = [res[2] for res in results]
        
        plt.figure(figsize=(10, 6))
        plt.plot(num_merges_vals, avg_lengths, marker='o', linestyle='-', linewidth=2, markersize=8)
        plt.title('Влияние количества BPE-слияний на среднюю длину токенизации', fontsize=14, fontweight='bold')
        plt.xlabel('Количество слияний', fontsize=12)
        plt.ylabel('Средняя длина токенизации', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(num_merges_vals)
        
        plt.savefig('bpe_experiment.png', dpi=300, bbox_inches='tight')
        print(f"\nГрафик сохранён в 'bpe_experiment.png'")
        
        print(f"\n{'='*60}")
        print("Готово! Все токенизаторы сохранены.")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
