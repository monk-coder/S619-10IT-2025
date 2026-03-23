"""
Обучение BPE токенизатора на data.txt
"""

import argparse
import matplotlib.pyplot as plt
from bpe import BPETokenizer


def load_text(filename):
    print(f"Загрузка {filename}...")
    
    encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']
    
    for enc in encodings:
        try:
            with open(filename, 'r', encoding=enc) as f:
                lines = [line.strip() for line in f if line.strip()]
            print(f"  Успешно: {enc}")
            return lines
        except UnicodeDecodeError:
            continue
    
    raise Exception(f"Не удалось прочитать файл {filename}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='data.txt', help='файл с текстом')
    parser.add_argument('--merges', default='0,2000,8000', help='список слияний')
    args = parser.parse_args()
    
    corpus = load_text(args.data)
    train = corpus[:int(len(corpus)*0.9)]
    val = corpus[int(len(corpus)*0.9):]
    
    merge_values = [int(x) for x in args.merges.split(',')]
    results = []
    
    print("\n" + "="*50)
    print("ОБУЧЕНИЕ BPE")
    print("="*50)
    
    for num in merge_values:
        print(f"\n--- Слияний: {num} ---")
        
        tok = BPETokenizer()
        tok.train(train, num_merges=num)
        tok.save(f'bpe_{num}')
        
        correct = 0
        total = min(100, len(val))
        lengths = []
        
        for text in val[:total]:
            ids = tok.encode(text)
            decoded = tok.decode(ids)
            lengths.append(len(ids))
            if decoded == text:
                correct += 1
        
        acc = correct / total * 100 if total > 0 else 0
        avg_len = sum(lengths) / len(lengths) if lengths else 0
        results.append((num, len(tok.vocab), avg_len, acc))
        
        print(f"Словарь: {len(tok.vocab)} токенов")
        print(f"Средняя длина: {avg_len:.1f} токенов")
        print(f"decode(encode(x)) == x: {acc:.1f}%")
    
    if results:
        plt.figure(figsize=(10, 5))
        x = [r[0] for r in results]
        y = [r[2] for r in results]
        
        plt.plot(x, y, 'bo-')
        plt.xlabel('Количество слияний')
        plt.ylabel('Средняя длина (токенов)')
        plt.title('BPE: зависимость длины от слияний')
        plt.grid(True)
        
        for i, (num, vocab, length, acc) in enumerate(results):
            plt.annotate(f'{length:.1f}', (x[i], y[i]), textcoords="offset points", xytext=(0,10), ha='center')
        
        plt.savefig('bpe_plot.png')
        print("\nГрафик сохранён: bpe_plot.png")
        plt.show()


if __name__ == '__main__':
    main()
