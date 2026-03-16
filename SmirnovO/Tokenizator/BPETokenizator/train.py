from tokenizer import BPETokenizer
import time


def run_experiment():
    with open('../data.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    # Split 90/10
    split_idx = int(len(text) * 0.9)
    train_text, val_text = text[:split_idx], text[split_idx:]

    for m in [0, 2000, 8000]:
        print(f"\n--- Experiment: num_merges = {m} ---")
        t = BPETokenizer()

        start = time.time()
        t.train(train_text, vocab_size=256 + m, verbose=False)
        end = time.time()

        val_ids = t.encode(val_text)

        # Метрики
        vocab_size = 256 + m
        avg_len = len(val_ids)
        top_1_percent_len = sorted([len(t.encode(w)) for w in val_text.split() if w])

        print(f"Обучено за: {end - start:.2f} сек")
        print(f"Размер словаря: {vocab_size}")
        print(f"Длина val (в токенах): {avg_len}")

        # Проверка на инвариантность
        assert t.decode(val_ids) == val_text, "Ошибка: decode(encode(x)) != x"
        print("Проверка decode(encode) пройдена успешно!")

        if m == 8000:  # Сохраняем лучшую версию
            t.save(".")


if __name__ == "__main__":
    run_experiment()
