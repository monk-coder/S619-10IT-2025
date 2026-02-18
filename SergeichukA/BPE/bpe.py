import json
import os
import sys
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import List, Tuple, Dict

# ============================================
# КЛАСС ТОКЕНИЗАТОРА
# ============================================

class BPETrainer:
    def __init__(self, vocab: List[str] = None, merges: List[Tuple[str, str]] = None):
        self.vocab = vocab if vocab is not None else []
        self.merges = merges if merges is not None else []
        self.token_to_id: Dict[str, int] = {}
        if vocab:
            self.token_to_id = {token: i for i, token in enumerate(vocab)}

    def get_stats(self, tokens: List[str]) -> Dict[Tuple[str, str], int]:
        """Подсчитывает частоту пар соседних токенов"""
        pairs = defaultdict(int)
        for i in range(len(tokens) - 1):
            pairs[(tokens[i], tokens[i + 1])] += 1
        return pairs

    def merge_tokens(self, tokens: List[str], pair: Tuple[str, str]) -> List[str]:
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

    def train(self, corpus: List[str], num_merges: int):
        """Обучает BPE токенизатор на корпусе"""
        print(f"\n[INFO] Начало обучения с {num_merges} слияниями...")
        
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
                print(f"[INFO] Прекращение обучения на шаге {i}: нет пар для слияния")
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
                print(f"[INFO] Выполнено {i + 1} слияний...")
        
        self.vocab = vocab
        self.merges = merges
        self.token_to_id = {token: i for i, token in enumerate(vocab)}
        
        print(f"[INFO] Обучение завершено. Размер словаря: {len(vocab)}")

    def encode(self, text: str) -> List[int]:
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

    def decode(self, ids: List[int]) -> str:
        """Декодирует последовательность токенов в текст"""
        tokens = []
        for id in ids:
            if id < len(self.vocab):
                tokens.append(self.vocab[id])
        return ''.join(tokens)

    def save(self, path: str):
        """Сохраняет токенизатор на диск"""
        os.makedirs(path, exist_ok=True)
        
        # Сохраняем словарь
        with open(os.path.join(path, 'vocab.txt'), 'w', encoding='utf-8') as f:
            for token in self.vocab:
                f.write(token + '\n')
        
        # Сохраняем правила слияния
        with open(os.path.join(path, 'merges.json'), 'w', encoding='utf-8') as f:
            json.dump(self.merges, f, ensure_ascii=False)
        
        print(f"[INFO] Токенизатор сохранён в {path}")

    @classmethod
    def load(cls, path: str):
        """Загружает токенизатор с диска"""
        vocab_path = os.path.join(path, 'vocab.txt')
        merges_path = os.path.join(path, 'merges.json')
        
        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab = [line.rstrip('\n') for line in f]
        
        with open(merges_path, 'r', encoding='utf-8') as f:
            merges = json.load(f)
        
        return cls(vocab=vocab, merges=merges)

# ============================================
# ФУНКЦИИ РАБОТЫ С ДАННЫМИ
# ============================================

def load_data(file_path: str, val_ratio: float = 0.1, output_dir: str = '.') -> Tuple[List[str], List[str]]:
    """Загружает данные и разделяет на тренировочную и валидационную выборки"""
    try:
        print(f"[INFO] Загрузка данных из {file_path}...")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден!")
        
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
        
        print(f"[INFO] Данные разделены: {len(train)} тренировочных, {len(val)} валидационных")
        return train, val
    
    except UnicodeDecodeError:
        print(f"[ERROR] Ошибка кодировки файла {file_path}. Убедитесь, что файл сохранён в UTF-8.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке данных: {e}")
        sys.exit(1)

# ============================================
# ФУНКЦИИ МЕТРИК
# ============================================

def compute_metrics(trainer: BPETrainer, val_corpus: List[str]) -> Tuple[int, float, float]:
    """Вычисляет метрики токенизатора"""
    try:
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
    
    except Exception as e:
        print(f"[ERROR] Ошибка при вычислении метрик: {e}")
        return len(trainer.vocab), 0.0, 0.0

# ============================================
# ФУНКЦИИ ВИЗУАЛИЗАЦИИ
# ============================================

def print_results_table(results: List[Tuple[int, int, float, float]]):
    """Выводит результаты в виде таблицы"""
    print(f"\n{'='*80}")
    print(f"{'ИТОГОВЫЕ РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТОВ':^80}")
    print(f"{'='*80}")
    header = f"{'Количество слияний':<20} {'Размер словаря':<20} {'Средняя длина':<20} {'Доля длинных':<20}"
    print(header)
    print(f"{'-'*80}")
    for num_merges, vocab_size, avg_length, share_long in results:
        print(f"{num_merges:<20} {vocab_size:<20} {avg_length:<20.2f} {share_long:<20.4f}")
    print(f"{'='*80}\n")

def plot_results(results: List[Tuple[int, int, float, float]], output_path: str = 'bpe_experiment.png'):
    """Строит график результатов"""
    try:
        num_merges_vals = [res[0] for res in results]
        avg_lengths = [res[2] for res in results]
        vocab_sizes = [res[1] for res in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # График 1: Средняя длина токенизации
        ax1.plot(num_merges_vals, avg_lengths, marker='o', linestyle='-', 
                 linewidth=2, markersize=8, color='blue')
        ax1.set_title('Средняя длина токенизации', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Количество слияний', fontsize=10)
        ax1.set_ylabel('Средняя длина', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(num_merges_vals)
        
        # График 2: Размер словаря
        ax2.plot(num_merges_vals, vocab_sizes, marker='s', linestyle='-', 
                 linewidth=2, markersize=8, color='green')
        ax2.set_title('Размер словаря', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Количество слияний', fontsize=10)
        ax2.set_ylabel('Размер словаря', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(num_merges_vals)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[INFO] Графики сохранены в '{output_path}'")
        plt.close()
    
    except ImportError:
        print(f"[WARNING] Библиотека matplotlib не установлена. Графики не будут построены.")
        print(f"[INFO] Установите её командой: pip install matplotlib")
    except Exception as e:
        print(f"[ERROR] Ошибка при построении графиков: {e}")

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Основная функция программы"""
    try:
        # Параметры
        data_file = 'data.txt'
        val_ratio = 0.1
        num_merges_list = [0, 2000, 8000]
        results = []
        
        # Загрузка данных
        train_corpus, val_corpus = load_data(data_file, val_ratio, '.')
        
        # Проводим эксперименты
        for num_merges in num_merges_list:
            try:
                print(f"\n{'='*80}")
                print(f"{'ЭКСПЕРИМЕНТ':^80}")
                print(f"{'='*80}")
                print(f"{'Параметры:':<20} Количество слияний = {num_merges}")
                
                # Обучение
                trainer = BPETrainer()
                trainer.train(train_corpus, num_merges)
                
                # Метрики
                vocab_size, avg_length, share_long = compute_metrics(trainer, val_corpus)
                
                # Тестирование
                test_text = "Hello world!"
                encoded = trainer.encode(test_text)
                decoded = trainer.decode(encoded)
                
                # Сохранение результатов
                results.append((num_merges, vocab_size, avg_length, share_long))
                
                # Сохранение токенизатора
                save_path = f'BPE_{num_merges}'
                trainer.save(save_path)
                
                # Вывод результатов эксперимента
                print(f"\n{'РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА':^80}")
                print(f"{'='*80}")
                print(f"{'Размер словаря:':<30} {vocab_size}")
                print(f"{'Средняя длина токенизации:':<30} {avg_length:.2f}")
                print(f"{'Доля длинных последовательностей:':<30} {share_long:.4%}")
                print(f"{'Тест кодирования:':<30} '{test_text}' -> {encoded}")
                print(f"{'Тест декодирования:':<30} {decoded}")
                print(f"{'='*80}\n")
            
            except Exception as e:
                print(f"[ERROR] Ошибка в эксперименте с {num_merges} слияниями: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Вывод итоговой таблицы
        if results:
            print_results_table(results)
            
            # Построение графиков
            plot_results(results)
            
            print(f"\n{'='*80}")
            print(f"{'ГОТОВО! Все токенизаторы сохранены.':^80}")
            print(f"{'='*80}\n")
            print(f"Сохранённые токенизаторы:")
            for num_merges in num_merges_list:
                print(f"  - BPE_{num_merges}/")
        
        else:
            print(f"[WARNING] Нет результатов для отображения")
    
    except KeyboardInterrupt:
        print(f"\n[INFO] Выполнение прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n[CRITICAL] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ============================================
# ТОЧКА ВХОДА
# ============================================

if __name__ == "__main__":
    main()
