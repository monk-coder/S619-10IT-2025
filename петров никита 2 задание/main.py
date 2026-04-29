import os
import random
import matplotlib.pyplot as plt
import numpy as np
from bpe_tokenizer import BPETokenizer

def find_data_file(start_dir, target_folder='0', target_file='data.txt'):
    """
    Ищет файл target_folder/target_file, поднимаясь вверх по дереву каталогов.
    Возвращает абсолютный путь или None, если не найден.
    """
    current = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(current, target_folder, target_file)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:  # Достигли корня файловой системы
            break
        current = parent
    return None

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

    for text in val_
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)
        
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
   
