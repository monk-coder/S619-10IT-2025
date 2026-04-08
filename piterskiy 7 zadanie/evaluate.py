from rag_pipeline import load_rag_system, get_answer_and_sources

QUESTIONS = [
    "Что такое causal mask в Transformer?",
    "Как работает механизм attention?",
    "В чем отличие между supervised и unsupervised learning?",
    "Что такое градиентный спуск?",
    "Объясните принцип работы сверточной нейросети (CNN).",
    "Что такое overfitting и как с ним бороться?",
    "Как работает алгоритм обратного распространения ошибки?",
    "В чем разница между L1 и L2 регуляризацией?",
    "Что такое dropout в нейронных сетях?",
    "Как оценивается качество модели машинного обучения?"
]

def evaluate():
    print("📊 Запуск оценки...")
    rag_chain, retriever = load_rag_system()
    scores = []
    
    for i, q in enumerate(QUESTIONS, 1):
        answer, sources = get_answer_and_sources(rag_chain, retriever, q)
        print(f"\n{'='*60}")
        print(f"Вопрос {i}: {q}")
        print(f"Источники: {[f\"{s['source']} (стр. {s['page']})\" for s in sources]}")
        print(f"Ответ: {answer}")
        print("Оцените вручную:")
        faithfulness = input("  Faithfulness (0/1): ").strip()
        relevance = input("  Relevance (0/1): ").strip()
        scores.append({"question": q, "faithfulness": int(faithfulness), "relevance": int(relevance)})

    faithfulness_rate = sum(s["faithfulness"] for s in scores) / len(scores) * 100
    relevance_rate = sum(s["relevance"] for s in scores) / len(scores) * 100

    print(f"\n{'='*60}")
    print("📈 Итоги:")
    print(f"Faithfulness Rate: {faithfulness_rate:.1f}%")
    print(f"Relevance Rate: {relevance_rate:.1f}%")
    
    with open("evaluation_results.txt", "w", encoding="utf-8") as f:
        f.write(f"Faithfulness Rate: {faithfulness_rate:.1f}%\n")
        f.write(f"Relevance Rate: {relevance_rate:.1f}%\n")
    print("📄 Результаты сохранены в evaluation_results.txt")

if __name__ == "__main__":
    evaluate()
