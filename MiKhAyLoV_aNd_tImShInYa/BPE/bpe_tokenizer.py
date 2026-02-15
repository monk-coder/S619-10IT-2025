"""
Это программа для обучения и использования BPE токенизатора.
Каждая часть кода подробно прокомментирована.
"""

# ИМПОРТ НЕОБХОДИМЫХ БИБЛИОТЕК
import json          # для сохранения токенизатора в файл
import re            # для работы с текстом (регулярные выражения)
from collections import Counter, defaultdict  # для подсчета частот
from typing import List, Dict, Tuple  # для указания типов данных
import numpy as np   # для математических вычислений
from tqdm import tqdm # для красивого прогресс-бара


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
        self.vocab = {}           # словарь: id -> токен (например, {5: "he"})
        self.inverse_vocab = {}   # словарь: токен -> id (например, {"he": 5})
        self.merges = {}           # правила слияния: пара -> новый токен
        self.special_tokens = {}   # специальные токены (<unk>, <pad> и т.д.)
        
    def _get_stats(self, words: List[List[str]]) -> Dict[Tuple[str, str], int]:
        """
        Подсчет частоты пар соседних символов
        -------------------------------------
        words: список слов, каждое слово - список символов
        возвращает: словарь {(символ1, символ2): частота}
        
        Пример: если есть слово ["h","e","l","l","o"]
        то пары: ("h","e"), ("e","l"), ("l","l"), ("l","o")
        """
        pairs = defaultdict(int)  # создаем словарь, где по умолчанию значение 0
        for word in words:        # проходим по каждому слову
            for i in range(len(word) - 1):  # идем по символам до предпоследнего
                pair = (word[i], word[i + 1])  # берем пару текущий+следующий
                pairs[pair] += 1                # увеличиваем счетчик для этой пары
        return dict(pairs)        # возвращаем как обычный словарь
    
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
        new_words = []  # здесь будут новые слова
        for word in words:  # для каждого слова
            new_word = []   # новое слово
            i = 0
            while i < len(word):  # пока не обработали все символы
                # если нашли пару для замены
                if i < len(word) - 1 and word[i] == pair[0] and word[i + 1] == pair[1]:
                    new_word.append(new_token)  # добавляем новый токен
                    i += 2  # пропускаем 2 символа
                else:
                    new_word.append(word[i])  # добавляем текущий символ
                    i += 1  # переходим к следующему
            new_words.append(new_word)  # добавляем готовое слово
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
            '<unk>': 0,  # неизвестный токен (если встретим символ, которого нет в словаре)
            '<pad>': 1,  # токен для выравнивания последовательностей
            '<s>': 2,    # начало предложения
            '</s>': 3    # конец предложения
        }
        
        # ШАГ 4: Создаем начальный словарь (спецтокены + все символы)
        self.vocab = {v: k for k, v in self.special_tokens.items()}  # спецтокены
        next_id = len(self.special_tokens)  # следующий свободный ID
        
        # Добавляем все символы в словарь
        for char in sorted(char_counts.keys()):
            self.vocab[next_id] = char
            next_id += 1
        
        # Создаем обратный словарь (токен -> id)
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
        
        # ШАГ 5: Представляем каждое слово как список символов
        print("Разбиение слов на символы...")
        words = [self._word_to_chars(word) for word in all_words]
        
        # ШАГ 6: ОСНОВНОЙ ЦИКЛ ОБУЧЕНИЯ - многократное слияние
        print(f"Начинаем слияние пар ({num_merges} итераций)...")
        self.merges = {}
        
        # Создаем прогресс-бар для визуализации процесса
        iterator = tqdm(range(num_merges), desc="Слияние пар") if verbose else range(num_merges)
        
        for i in iterator:
            # Подсчитываем частоты всех пар
            pairs = self._get_stats(words)
            
            if not pairs:  # если нет больше пар для слияния
                print(f"Нет больше пар для слияния на шаге {i}")
                break
            
            # Находим самую частую пару
            most_frequent_pair = max(pairs.items(), key=lambda x: x[1])[0]
            
            # Создаем новый токен (просто соединяем два символа)
            new_token = ''.join(most_frequent_pair)
            
            # Запоминаем правило слияния
            self.merges[most_frequent_pair] = new_token
            
            # Добавляем новый токен в словарь
            self.vocab[next_id] = new_token
            self.inverse_vocab[new_token] = next_id
            next_id += 1
            
            # Применяем слияние ко всем словам
            words = self._merge_pair(words, most_frequent_pair, new_token)
            
            # Обновляем описание в прогресс-баре (показываем последнюю пару)
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
        # Разбиваем текст на слова
        words = self._preprocess_text(text)
        
        # Здесь будут все токены
        encoded_tokens = []
        
        # Кодируем каждое слово отдельно
        for word in words:
            # Начинаем с отдельных символов
            tokens = self._word_to_chars(word)
            
            # Применяем все правила слияния (в порядке их создания)
            # Продолжаем, пока есть что объединять
            changed = True
            while changed:
                changed = False
                i = 0
                while i < len(tokens) - 1:
                    # Проверяем, можно ли объединить текущую пару
                    pair = (tokens[i], tokens[i + 1])
                    if pair in self.merges:
                        # Объединяем!
                        tokens = tokens[:i] + [self.merges[pair]] + tokens[i + 2:]
                        changed = True
                    else:
                        i += 1
            
            # Преобразуем токены в ID
            for token in tokens:
                if token in self.inverse_vocab:
                    encoded_tokens.append(self.inverse_vocab[token])
                else:
                    # Если токен не найден, используем <unk>
                    encoded_tokens.append(self.special_tokens['<unk>'])
        
        # Добавляем специальные токены если нужно
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
        # Преобразуем ID обратно в токены
        tokens = []
        special_ids = set(self.special_tokens.values())  # множество ID спецтокенов
        
        for token_id in ids:
            # Пропускаем спецтокены если нужно
            if skip_special_tokens and token_id in special_ids:
                continue
            
            # Ищем токен по ID
            if token_id in self.vocab:
                tokens.append(self.vocab[token_id])
            else:
                # Если ID не найден, используем <unk>
                tokens.append('<unk>')
        
        # Объединяем все токены в текст
        text = ''.join(tokens)
        
        return text
    
    def save(self, path: str) -> None:
        """
        СОХРАНЕНИЕ ТОКЕНИЗАТОРА В ФАЙЛ
        -------------------------------
        path: путь к файлу (например, "my_tokenizer.json")
        """
        # Подготавливаем данные для сохранения
        data = {
            'vocab': self.vocab,  # словарь
            'merges': {f"{k[0]}||{k[1]}": v for k, v in self.merges.items()},  # правила слияния
            'special_tokens': self.special_tokens  # спецтокены
        }
        
        # Сохраняем в JSON файл
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
        
        # Восстанавливаем словарь (ключи ID должны быть числами)
        self.vocab = {int(k): v for k, v in data['vocab'].items()}
        
        # Восстанавливаем правила слияния
        self.merges = {}
        for k, v in data['merges'].items():
            parts = k.split('||')
            self.merges[(parts[0], parts[1])] = v
        
        # Восстанавливаем спецтокены
        self.special_tokens = data['special_tokens']
        
        # Создаем обратный словарь
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
    # Читаем файл
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]  # убираем пустые строки
    
    print(f"Загружено {len(lines)} строк из файла")
    
    # Перемешиваем данные для случайного разбиения
    np.random.seed(42)  # фиксируем seed для воспроизводимости
    indices = np.random.permutation(len(lines))
    
    # Вычисляем границу разделения
    split_idx = int(len(lines) * train_ratio)
    
    # Разделяем на train и val
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
    
    token_lengths = []  # длины последовательностей
    
    for i, text in enumerate(val_data):
        # Кодируем текст
        encoded = tokenizer.encode(text)
        token_lengths.append(len(encoded))
        
        # Показываем прогресс
        if (i + 1) % 10 == 0:
            print(f"Обработано {i+1}/{len(val_data)} примеров")
    
    # Вычисляем метрики
    metrics = {
        'vocab_size': len(tokenizer.vocab),  # размер словаря
        'avg_token_length': np.mean(token_lengths),  # средняя длина
        'std_token_length': np.std(token_lengths),   # стандартное отклонение
        'max_token_length': np.max(token_lengths),   # максимум
        'min_token_length': np.min(token_lengths),   # минимум
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
        
        # Создаем и обучаем токенизатор
        tokenizer = BPETokenizer()
        tokenizer.train(train_data, num_merges=num_merges, verbose=True)
        
        # Оцениваем его
        metrics = evaluate_tokenizer(tokenizer, val_data)
        results.append((num_merges, metrics))
        
        # Выводим результаты
        print(f"\nРезультаты для num_merges = {num_merges}:")
        print(f"  Размер словаря: {metrics['vocab_size']}")
        print(f"  Средняя длина: {metrics['avg_token_length']:.2f}")
        print(f"  Доля очень длинных: {metrics['very_long_ratio']:.2%}")
    
    # Сводная таблица
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
    
    # Путь к файлу с данными
    data_file = "data.txt"  # файл должен быть в той же папке
    
    try:
        # ШАГ 1: Подготовка данных
        print("\n1. ПОДГОТОВКА ДАННЫХ")
        print("-" * 30)
        train_data, val_data = prepare_data(data_file)
        
        # ШАГ 2: Обучение токенизатора
        print("\n2. ОБУЧЕНИЕ ТОКЕНИЗАТОРА")
        print("-" * 30)
        tokenizer = BPETokenizer()
        tokenizer.train(train_data, num_merges=500, verbose=True)  # 500 слияний
        
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
        metrics = evaluate_tokenizer(loaded_tokenizer, val_data[:50])  # на первых 50 примерах
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
        # Используем меньше данных для быстроты
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