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


def run_experiment(data_path, merge_values, output_base="tokenizer"):
    results = []
    
    print("\n" + "="*60)
    print("🔬 ЭКСПЕРИМЕНТ: влияние num_merges на длину токенизации")
    print("="*60)
    
    for i, num_merges in enumerate(merge_values):
        print(f"\n[{i+1}/{len(merge_values)}] Обучение с num_merges={num_merges}")
        
        tokenizer = BPETokenizer()
        tokenizer.train(
            data_path,
            num_merges=num_merges,
            val_split=0.1,
            show_progress=False  
        )
        
        res = evaluate_tokenizer(
            tokenizer,
            tokenizer.val_lines,
            desc=f"Оценка (nm={num_merges})"
        )
        
        output_path = f"{output_base}_nm{num_merges}.json"
        tokenizer.save(output_path)
        
        results.append({
            "num_merges": num_merges,
            "vocab_size": res["vocab_size"],
            "avg_len": res["avg_len"]
        })
        
        print(f"  → vocab_size: {res['vocab_size']:5d} | avg_len: {res['avg_len']:6.2f} токенов | сохранено: {output_path}")
    
    return results


def plot_experiment(results, save_path="experiment.png"):
    merge_vals = [r["num_merges"] for r in results]
    avg_lens = [r["avg_len"] for r in results]
    vocab_sizes = [r["vocab_size"] for r in results]
    
    plt.figure(figsize=(10, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(merge_vals, avg_lens, 'o-', color='#2E86AB', linewidth=2, markersize=8)
    plt.xlabel("num_merges", fontsize=11)
    plt.ylabel("Средняя длина (токены)", fontsize=11)
    plt.title("Длина последовательности", fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(merge_vals, vocab_sizes, 's-', color='#A23B72', linewidth=2, markersize=8)
    plt.xlabel("num_merges", fontsize=11)
    plt.ylabel("Размер словаря", fontsize=11)
    plt.title("Размер словаря", fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n📈 Графики сохранены: {save_path}")


def demo_encoding(tokenizer)
    print("\n" + "="*60)
    print("🧪 ДЕМОНСТРАЦИЯ: кодирование и декодирование")
    print("="*60)
    
    if tokenizer.val_lines:
        test_text = tokenizer.val_lines[0]
    else:
        test_text = "Привет, мир! Это тест BPE токенизатора."
    
    print(f"\nИсходный текст:\n  '{test_text}'")
    
    ids = tokenizer.encode(test_text)
    print(f"\nТокены (ID):\n  {ids}")
    
    tokens_str = [tokenizer._inv_vocab.get(i, '<?>') for i in ids]
    print(f"\nТокены (строки):\n  {tokens_str}")
    
    decoded = tokenizer.decode(ids)
    print(f"\nДекодированный текст:\n  '{decoded}'")
    
    is_reversible = decoded == test_text
    print(f"\n✅ Обратимость: {'УСПЕШНО' if is_reversible else 'ОШИБКА'}")
    
    return is_reversible


def main():
    parser = argparse.ArgumentParser(description="BPE Tokenizer — обучение и анализ")
    parser.add_argument("--num_merges", type=int, default=2000, help="Количество слияний")
    parser.add_argument("--data_path", type=str, default="data.txt", help="Путь к корпусу")
    parser.add_argument("--output", type=str, default="tokenizer.json", help="Файл для сохранения")
    parser.add_argument("--run_experiment", action="store_true", help="Запустить эксперимент с разными num_merges")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🚀 BPE TOKENIZER — обучение с нуля")
    print("="*60)
    print(f"📁 Корпус: {args.data_path}")
    print(f"🔄 Слияний: {args.num_merges}")
    print(f"💾 Выход: {args.output}")
    
    print("\n" + "-"*60)
    print("📚 ЭТАП 1: Обучение токенизатора")
    print("-"*60)
    tokenizer = BPETokenizer()
    tokenizer.train(
        args.data_path,
        num_merges=args.num_merges,
        val_split=0.1,
        show_progress=True
    )
    
    tokenizer.save(args.output)
    print(f"✅ Модель сохранена: {args.output}")
    
    print("\n" + "-"*60)
    print("🔍 ЭТАП 2: Проверка обратимости и метрики")
    print("-"*60)
    results = evaluate_tokenizer(tokenizer, tokenizer.val_lines, desc="Валидация")
    
    print("\n📊 Метрики на валидационном наборе:")
    print(f"  • Размер словаря:    {results['vocab_size']}")
    print(f"  • Средняя длина:     {results['avg_len']:.2f} токенов")
    print(f"  • 99-перцентиль:     {results['top1p_len']:.1f} токенов")
    print(f"  • Макс. длина:       {results['max_len']} токенов")
    print(f"  • Примеров:          {results['total_samples']}")
    
    demo_encoding(tokenizer)
    
    if args.run_experiment:
        print("\n" + "-"*60)
        print("🔬 ЭТАП 3: Эксперимент с разными num_merges")
        print("-"*60)
        merge_values = [0, 500, 2000]
        exp_results = run_experiment(args.data_path, merge_values)
        plot_experiment(exp_results)
    
    print("\n" + "="*60)
    print("✅ ВСЁ ГОТОВО! Токенизатор обучен и протестирован.")
    print("="*60)


if __name__ == "__main__":
    main()
