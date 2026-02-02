import argparse
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from bpe_tokenizer import BPETokenizer


def evaluate_tokenizer(tokenizer, lines, desc="Оценка"):
    lengths = []
    for line in tqdm(lines, desc=desc):
        ids = tokenizer.encode(line)
        decoded = tokenizer.decode(ids)
        if decoded != line:
            print(f"\n❌ Ошибка обратимости!")
            print(f"Оригинал: '{line}'")
            print(f"Декод:    '{decoded}'")
            print(f"IDs: {ids}")
            raise AssertionError(f"decode(encode(x)) != x для строки: '{line[:50]}'")
        lengths.append(len(ids))
    
    lengths = np.array(lengths)
    return {
        "vocab_size": len(tokenizer.vocab),
        "avg_len": float(lengths.mean()),
        "top1p_len": float(np.percentile(lengths, 99)),
        "max_len": int(lengths.max()),
        "total_samples": len(lines)
    }


def main():
    parser = argparse.ArgumentParser(description="Обучение BPE токенизатора")
    parser.add_argument("--num_merges", type=int, default=2000, help="Количество слияний")
    parser.add_argument("--data_path", type=str, default="data.txt", help="Путь к корпусу")
    parser.add_argument("--output", type=str, default="tokenizer.json", help="Файл для сохранения")
    args = parser.parse_args()

    print(f"📚 Обучение BPE с num_merges={args.num_merges}...")
    tokenizer = BPETokenizer()
    tokenizer.train(args.data_path, num_merges=args.num_merges)
    tokenizer.save(args.output)
    print(f"✅ Токенизатор сохранён в {args.output}")

    print("\n🔍 Проверка обратимости на val...")
    results = evaluate_tokenizer(tokenizer, tokenizer.val_lines, desc="Проверка val")
    
    print("\n📊 Результаты на валидации:")
    print(f"  Размер словаря:       {results['vocab_size']}")
    print(f"  Средняя длина:        {results['avg_len']:.2f} токенов")
    print(f"  99-перцентиль:        {results['top1p_len']:.1f} токенов")
    print(f"  Макс. длина:          {results['max_len']} токенов")
    print(f"  Всего примеров:       {results['total_samples']}")

    print("\n🔬 Эксперимент: сравнение разных num_merges")
    merge_vals = [0, 500, 2000]
    avg_lengths = []
    vocab_sizes = []

    for nm in merge_vals:
        print(f"\nОбучение с num_merges={nm}...")
        tok = BPETokenizer()
        tok.train(args.data_path, num_merges=nm)
        res = evaluate_tokenizer(tok, tok.val_lines, desc=f"nm={nm}")
        avg_lengths.append(res["avg_len"])
        vocab_sizes.append(res["vocab_size"])
        print(f"  → vocab_size={res['vocab_size']}, avg_len={res['avg_len']:.2f}")

    plt.figure(figsize=(8, 5))
    plt.plot(merge_vals, avg_lengths, 'o-', linewidth=2, markersize=8)
    plt.xlabel("num_merges", fontsize=12)
    plt.ylabel("Средняя длина последовательности (токены)", fontsize=12)
    plt.title("Влияние количества слияний на длину токенизации", fontsize=13)
    plt.grid(True, alpha=0.3)
    plt.savefig("experiment.png", dpi=150, bbox_inches='tight')
    print("\n📈 График сохранён: experiment.png")

    print("\n🧪 Пример кодирования/декодирования:")
    test_text = tokenizer.val_lines[0] if tokenizer.val_lines else "Привет, мир!"
    ids = tokenizer.encode(test_text)
    decoded = tokenizer.decode(ids)
    print(f"Текст:    '{test_text}'")
    print(f"IDs:      {ids[:20]}{'...' if len(ids) > 20 else ''}")
    print(f"Декод:    '{decoded}'")
    print(f"✅ Обратимость: {decoded == test_text}")


if __name__ == "__main__":
    main()
