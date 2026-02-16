"""
Это программа для обучения и использования BPE токенизатора.
Каждая часть кода подробно прокомментирована.
"""

# ИМПОРТ НЕОБХОДИМЫХ БИБЛИОТЕК
import json
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import numpy as np
from tqdm import tqdm


class BPETokenizer:
    """
    КЛАСС ТОКЕНИЗАТОРА
    -------------------
    Здесь хранятся все методы для работы с токенизатором:
    - train: обучение на текстах
    - encode: превращение текста в числа
    - decode: превращение чисел обратно в текст
    - save: сохранение в файл
    - load: загрузка из файла
    """
    
    def __init__(self):
        """Конструктор - вызывается при создании токенизатора"""
        self.vocab = {}
        self.inverse_vocab = {}  
        self.merges = {}       
        self.special_tokens = {}  
        
    def _get_stats(self, words: List[List[str]]) -> Dict[Tuple[str, str], int]:
        """
        Подсчет частоты пар соседних символов
        -------------------------------------
        words: список слов, каждое слово - список символов
        возвращает: словарь {(символ1, символ2): частота}
        
        Пример: если есть слово ["h","e","l","l","o"]
        то пары: ("h","e"), ("e","l"), ("l","l"), ("l","o")
        """
        pairs = defaultdict(int) 
        for word in words:       
            for i in range(len(word) - 1): 
                pair = (word[i], word[i + 1]) 
                pairs[pair] += 1          
        return dict(pairs)    
    
    def _merge_pair(self, words: List[List[str]], pair: Tuple[str, str], new_token: str) -> List[List[str]]:
        """
        Замена всех вхождений пары на новый токен
        -----------------------------------------
        words: список слов
        pair: пара для замены (например, ("h","e"))
        new_token: новый токен (например, "he")
        возвращает: обновленный список слов
        
        Пример: слово ["h","e","l","l","o"], пара ("h","e"), новый токен "he"
        результат: ["he","l","l","o"]
        """
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
        """
        Предобработка текста: нормализация пробелов и разбиение на слова
        ----------------------------------------------------------------
        text: входной текст
        возвращает: список слов
        
        Пример: "Hello  world!" -> ["Hello", "world!"]
        """
        # Заменяем несколько пробелов на один
        text = re.sub(r'\s+', ' ', text.strip())
        # Разбиваем на слова по пробелам
        return text.split()
    
    def _word_to_chars(self, word: str) -> List[str]:
        """
        Преобразование слова в список символов
        --------------------------------------
        word: слово (например, "hello")
        возвращает: список символов (["h","e","l","l","o"])
        """
        return list(word)
    
    def train(self, corpus: List[str], num_merges: int, verbose: bool = True) -> 'BPETokenizer':
        """
        ОБУЧЕНИЕ ТОКЕНИЗАТОРА - САМАЯ ВАЖНАЯ ЧАСТЬ
        --------------------------------------------
        corpus: список текстов для обучения
        num_merges: сколько раз объединять пары
        verbose: показывать ли прогресс
        
        Алгоритм BPE:
        1. Начинаем с отдельных символов
        2. Находим самую частую пару соседних символов
        3. Объединяем их в один токен
        4. Повторяем шаги 2-3 num_merges раз
        """
        
        # ШАГ 1: Собираем все слова из корпуса
        print("Сбор всех слов из корпуса...")
        all_words = []
        for text in corpus:
            all_words.extend(self._preprocess_text(text))
        
        # ШАГ 2: Считаем все символы, чтобы создать начальный словарь
        print("Подсчет символов...")
        char_counts = Counter()
        for word in all_words:
            char_counts.update(self._word_to_chars(word))
        
        # ШАГ 3: Создаем специальные токены
        self.special_tokens = {
            '<unk>': 0,  
            '<pad>': 1, 
            '<s>': 2,  
            '</s>': 3  
        }
        
        # ШАГ 4: Создаем начальный словарь (спецтокены + все символы)
        self.vocab = {v: k for k, v in self.special_tokens.items()} 
        next_id = len(self.special_tokens) 
        
        for char in sorted(char_counts.keys()):
            self.vocab[next_id] = char
            next_id += 1
        
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
        
        # ШАГ 5: Представляем каждое слово как список символов
        print("Разбиение слов на символы...")
        words = [self._word_to_chars(word) for word in all_words]
        
        # ШАГ 6: ОСНОВНОЙ ЦИКЛ ОБУЧЕНИЯ - многократное слияние
        print(f"Начинаем слияние пар ({num_merges} итераций)...")
        self.merges = {}
        
        iterator = tqdm(range(num_merges), desc="Слияние пар") if verbose else range(num_merges)
        
        for i in iterator:
            pairs = self._get_stats(words)
            
            if not pairs: 
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
        
        print(f"Обучение завершено! Размер словаря: {len(self.vocab)}")
        return self
    
    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        """
        КОДИРОВАНИЕ ТЕКСТА В ЧИСЛА
        ---------------------------
        text: текст для кодирования
        add_special_tokens: добавлять ли <s> в начало и </s> в конец
        возвращает: список чисел (ID токенов)
        
        Пример: "hello" -> [5, 6, 7, 7, 8] (если h=5, e=6, l=7, o=8)
        """
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
            result = [self.special_tokens['<s>']] + encoded_tokens + [self.special_tokens['</s>']]
            return result
        
        return encoded_tokens
    
    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        ДЕКОДИРОВАНИЕ ЧИСЕЛ ОБРАТНО В ТЕКСТ
        ------------------------------------
        ids: список чисел (ID токенов)
        skip_special_tokens: пропускать ли специальные токены
        возвращает: восстановленный текст
        
        Пример: [5,6,7,7,8] -> "hello"
        """
        tokens = []
        special_ids = set(self.special_tokens.values())
        
        for token_id in ids:
            if skip_special_tokens and token_id in special_ids:
                continue
            
            if token_id in self.vocab:
                tokens.append(self.vocab[token_id])
            else:
                tokens.append('<unk>')
        
        text = ''.join(tokens)
        
        return text
    
    def save(self, path: str) -> None:
        """
        СОХРАНЕНИЕ ТОКЕНИЗАТОРА В ФАЙЛ
        -------------------------------
        path: путь к файлу (например, "my_tokenizer.json")
        """
        data = {
            'vocab': self.vocab,
            'merges': {f"{k[0]}||{k[1]}": v for k, v in self.merges.items()},
            'special_tokens': self.special_tokens
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Токенизатор сохранен в {path}")
    
    def load(self, path: str) -> 'BPETokenizer':
        """
        ЗАГРУЗКА ТОКЕНИЗАТОРА ИЗ ФАЙЛА
        -------------------------------
        path: путь к файлу
        возвращает: загруженный токенизатор
        """
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
    """
    ПОДГОТОВКА ДАННЫХ: РАЗБИЕНИЕ НА ОБУЧАЮЩУЮ И ПРОВЕРОЧНУЮ ВЫБОРКИ
    -----------------------------------------------------------------
    file_path: путь к файлу с данными
    train_ratio: доля данных для обучения (0.9 = 90%)
    возвращает: (train_data, val_data) - списки текстов
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"Загружено {len(lines)} строк из файла")
    
    np.random.seed(42)  
    indices = np.random.permutation(len(lines))
    
    split_idx = int(len(lines) * train_ratio)
    
    train_indices = indices[:split_idx]
    val_indices = indices[split_idx:]
    
    train_data = [lines[i] for i in train_indices]
    val_data = [lines[i] for i in val_indices]
    
    print(f"Обучающих примеров: {len(train_data)}")
    print(f"Проверочных примеров: {len(val_data)}")
    
    return train_data, val_data


def evaluate_tokenizer(tokenizer: BPETokenizer, val_data: List[str]) -> Dict:
    """
    ОЦЕНКА КАЧЕСТВА ТОКЕНИЗАТОРА
    ----------------------------
    tokenizer: обученный токенизатор
    val_data: проверочные данные
    возвращает: словарь с метриками
    """
    print("Оценка токенизатора...")
    
    token_lengths = []
    
    for i, text in enumerate(val_data):
        encoded = tokenizer.encode(text)
        token_lengths.append(len(encoded))
        
        if (i + 1) % 10 == 0:
            print(f"Обработано {i+1}/{len(val_data)} примеров")
    
    metrics = {
        'vocab_size': len(tokenizer.vocab), 
        'avg_token_length': np.mean(token_lengths), 
        'std_token_length': np.std(token_lengths), 
        'max_token_length': np.max(token_lengths),  
        'min_token_length': np.min(token_lengths), 
    }
    
    # Вычисляем долю очень длинных последовательностей (топ 1%)
    percentile_99 = np.percentile(token_lengths, 99)
    very_long_count = sum(1 for l in token_lengths if l > percentile_99)
    metrics['very_long_ratio'] = very_long_count / len(token_lengths) if token_lengths else 0
    
    return metrics


def experiment_different_merges(train_data: List[str], val_data: List[str], merge_values: List[int]) -> None:
    """
    ЭКСПЕРИМЕНТ С РАЗНЫМ КОЛИЧЕСТВОМ СЛИЯНИЙ
    -----------------------------------------
    train_data: обучающие данные
    val_data: проверочные данные
    merge_values: список значений num_merges для сравнения
    """
    print("\n" + "="*60)
    print("ЭКСПЕРИМЕНТ: Сравнение разных значений num_merges")
    print("="*60)
    
    results = []
    
    for num_merges in merge_values:
        print(f"\n--- Обучение с num_merges = {num_merges} ---")
        
        tokenizer = BPETokenizer()
        tokenizer.train(train_data, num_merges=num_merges, verbose=True)
        
        metrics = evaluate_tokenizer(tokenizer, val_data)
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


def main():
    """
    ГЛАВНАЯ ФУНКЦИЯ - ЗДЕСЬ ВСЁ НАЧИНАЕТСЯ
    """
    print("="*60)
    print("BPE ТОКЕНИЗАТОР - ДЕМОНСТРАЦИЯ РАБОТЫ")
    print("="*60)
    
    data_file = "data.txt"
    
    try:
        # ШАГ 1: Подготовка данных
        print("\n1. ПОДГОТОВКА ДАННЫХ")
        print("-" * 30)
        train_data, val_data = prepare_data(data_file)
        
        # ШАГ 2: Обучение токенизатора
        print("\n2. ОБУЧЕНИЕ ТОКЕНИЗАТОРА")
        print("-" * 30)
        tokenizer = BPETokenizer()
        tokenizer.train(train_data, num_merges=500, verbose=True) 
        
        # ШАГ 3: Сохранение токенизатора
        print("\n3. СОХРАНЕНИЕ ТОКЕНИЗАТОРА")
        print("-" * 30)
        tokenizer.save("bpe_tokenizer.json")
        
        # ШАГ 4: Загрузка токенизатора (проверка, что сохранение работает)
        print("\n4. ЗАГРУЗКА ТОКЕНИЗАТОРА")
        print("-" * 30)
        loaded_tokenizer = BPETokenizer()
        loaded_tokenizer.load("bpe_tokenizer.json")
        
        # ШАГ 5: Демонстрация encode/decode
        print("\n5. ДЕМОНСТРАЦИЯ ENCODE/DECODE")
        print("-" * 30)
        test_texts = [
            "Hello world!",
            "This is a test sentence.",
            "BPE tokenization is interesting.",
            "The quick brown fox jumps over the lazy dog."
        ]
        
        for text in test_texts:
            print(f"\nИсходный текст: {text}")
            encoded = loaded_tokenizer.encode(text)
            print(f"Закодировано: {encoded[:10]}{'...' if len(encoded) > 10 else ''} (всего {len(encoded)} токенов)")
            decoded = loaded_tokenizer.decode(encoded)
            print(f"Декодировано: {decoded}")
        
        # ШАГ 6: Оценка на валидационных данных
        print("\n6. ОЦЕНКА НА ВАЛИДАЦИОННЫХ ДАННЫХ")
        print("-" * 30)
        metrics = evaluate_tokenizer(loaded_tokenizer, val_data[:50]) 
        print(f"\nРезультаты оценки:")
        print(f"  Размер словаря: {metrics['vocab_size']}")
        print(f"  Средняя длина последовательности: {metrics['avg_token_length']:.2f}")
        print(f"  Стандартное отклонение: {metrics['std_token_length']:.2f}")
        print(f"  Макс длина: {metrics['max_token_length']}")
        print(f"  Мин длина: {metrics['min_token_length']}")
        print(f"  Доля очень длинных (топ 1%): {metrics['very_long_ratio']:.2%}")
        
        # ШАГ 7: Эксперимент с разными значениями num_merges
        print("\n7. ЭКСПЕРИМЕНТ С РАЗНЫМИ ЗНАЧЕНИЯМИ NUM_MERGES")
        print("-" * 30)
        experiment_different_merges(train_data[:100], val_data[:20], [0, 100, 500])
        
    except FileNotFoundError:
        print(f"\nОШИБКА: Файл '{data_file}' не найден!")
        print(f"Пожалуйста, создайте файл '{data_file}' в папке {__file__}")
        print("\nПример содержимого файла:")
        print("-" * 30)
        print("The quick brown fox jumps over the lazy dog.")
        print("Machine learning is a subset of artificial intelligence.")
        print("Natural language processing helps computers understand human language.")
        print("-" * 30)


if __name__ == "__main__":

    main()
