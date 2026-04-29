import os
import random
import matplotlib.pyplot as plt
import numpy as np
from bpe_tokenizer import BPETokenizer

def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл не найден: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip()]

def split_data(lines, test_ratio=0.1):
    random.seed(42)
    random.shuffle(lines)
    split_idx = int(len(lines) * (1 - test_ratio))
    return lines[:split_idx], lines[split_idx:]

def evaluate_tokenizer(tokenizer, val_data):
    total_len = 0
    lengths = []
    errors = 0

    for text in val_data:
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)
        
        # Строгая проверка условия
        if decoded != text:
            errors += 1
            
        total_len += len(encoded)
        lengths.append(len(encoded))

    avg_len = total_len / len(val_data) if val_data else 0
    long_ratio = 0
    if lengths:
        threshold = np.percentile(lengths, 99)
        long_ratio = sum(1 for l in lengths if l > threshold) / len(lengths)

    return {
        "avg_length": avg_len,
        "vocab_size": len(tokenizer.vocab),
        "errors": errors,
        "long_tokenization_ratio": long_ratio
    }

def experiment_with_merges(train_data, val_data, merge_counts=[0, 500, 1000, 2000]):
    results = []
    for num_merges in merge_counts:
        print(f"\n--- Experiment: num_merges={num_merges} ---")
        tokenizer = BPETokenizer()
        tokenizer.train(train_data, num_merges=num_merges)
        metrics = evaluate_tokenizer(tokenizer, val_data)
        metrics['num_merges'] = num_merges
        results.append(metrics)
        print(f"Vocab: {metrics['vocab_size']} | Avg Len: {metrics['avg_length']:.2f} | Errors: {metrics['errors']}")
    return results

def plot_results(results):
    merges = [r['num_merges'] for r in results]
    avg_lengths = [r['avg_length'] for r in results]
    vocab_sizes = [r['vocab_size'] for r in results]

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(merges, avg_lengths, marker='o', color='b')
    plt.title('Average Token Length vs Num Merges')
    plt.xlabel('Num Merges'); plt.ylabel('Avg Tokens per Sentence'); plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(merges, vocab_sizes, marker='s', color='orange')
    plt.title('Vocabulary Size vs Num Merges')
    plt.xlabel('Num Merges'); plt.ylabel('Vocab Size'); plt.grid(True)

    plt.tight_layout()
    plt.savefig('bpe_metrics.png')
    plt.show()
    print("График сохранен как bpe_metrics.png")

def main():
    # 📍 Надежное определение пути к data.txt
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir)) # BPE -> Личная папка -> Корень
    data_path = os.path.join(repo_root, '0', 'data.txt')

    print(f"🔍 Поиск данных: {data_path}")
    if not os.path.exists(data_path):
        local_path = os.path.join(script_dir, '0', 'data.txt')
        if os.path.exists(local_path):
            data_path = local_path
        else:
            print("❌ Ошибка: data.txt не найден. Проверьте структуру папок.")
            return

    print("📥 Загрузка данных...")
    lines = load_data(data_path)
    train_data, val_data = split_data(lines)
    print(f"✅ Train: {len(train_data)} | Val: {len(val_data)}")

    # 1. Финальное обучение
    print("\n🚀 Обучение финальной
