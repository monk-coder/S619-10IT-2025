from rag_pipeline import RAGPipeline

# ВАЖНО: замените эти вопросы на свои (по вашим PDF)!
TEST_QUESTIONS = [
    "Что такое causal mask?",
    "Чем RNN отличаются от трансформеров?",
    "Что такое attention?",
    "Что такое fine-tuning?",
    "Как работает Layer Normalization?",
    "Что такое позиционное кодирование?",
    "Что такое перплексия?",
    "Какие функции активации используются?",
    "Что такое Llama?",
    "Что такое семплирование?"
]

def main():
    pipeline = RAGPipeline()
    results = []
    
    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"\n--- {i}. {q} ---")
        answer, sources = pipeline.ask(q)
        print(f"Ответ: {answer[:200]}...")
        print("Источники:", [s.metadata.get('source', '?') for s in sources])
        
        f = int(input("Faithfulness (0/1): "))
        r = int(input("Relevance (0/1): "))
        results.append((f, r))
    
    faithful_rate = sum(r[0] for r in results) / len(results) * 100
    relevance_rate = sum(r[1] for r in results) / len(results) * 100
    
    print(f"\nFaithfulness: {faithful_rate:.1f}%")
    print(f"Relevance: {relevance_rate:.1f}%")
    print("Пройдено!" if faithful_rate >= 70 else "Не пройдено")

if __name__ == "__main__":
    main()