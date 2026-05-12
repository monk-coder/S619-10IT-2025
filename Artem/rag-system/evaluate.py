from rag_pipeline import setup_rag_pipeline

# ЗАМЕНИТЕ НА 10 ВОПРОСОВ ПО ВАШИМ PDF
TEST_QUESTIONS = [
    "Что такое causal mask в Transformer?",
    "Как работает механизм self-attention?",
    "В чем разница между fine-tuning и prompt engineering?",
    "Какие архитектуры нейросетей обсуждаются в лекциях?",
    "Как оценивается качество эмбеддингов?",
    "Что такое hallucination в LLM?",
    "Какие методы регуляризации упоминаются?",
    "Как работает backpropagation?",
    "Что такое zero-shot классификация?",
    "Какие ограничения есть у FAISS индексации?"
]

def evaluate():
    print("📊 Загрузка системы для оценки...")
    chain, db = setup_rag_pipeline()

    results = []
    print("\n" + "="*50)
    print("ОЦЕНКА КАЧЕСТВА ОТВЕТОВ")
    print("Faithfulness (0/1): Ответ строго следует контексту?")
    print("Relevance (0/1): Найденные чанки релевантны вопросу?")
    print("="*50)

    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"\n🔹 Вопрос {i}: {q}")
        docs = db.as_retriever(search_kwargs={"k": 3}).invoke(q)
        print("📎 Источники:")
        for d in docs:
            print(f"   - {d.metadata.get('source_file', '?')} стр. {d.metadata.get('page', '?')}")
        
        ans = chain.invoke(q)
        print(f"💬 Ответ: {ans}")

        while True:
            try:
                f = int(input("Faithfulness (0 или 1): "))
                r = int(input("Relevance (0 или 1): "))
                if f in (0, 1) and r in (0, 1):
                    break
                print("Введите 0 или 1.")
            except ValueError:
                print("Некорректный ввод. Попробуйте снова.")
        
        results.append({"faithfulness": f, "relevance": r})
        print("✅ Оценено.")

    f_rate = sum(r["faithfulness"] for r in results) / len(results) * 100
    r_rate = sum(r["relevance"] for r in results) / len(results) * 100

    print("\n" + "="*50)
    print("📈 ИТОГИ ОЦЕНКИ")
    print(f"Faithfulness Rate: {f_rate:.1f}%")
    print(f"Relevance Rate: {r_rate:.1f}%")
    status = "✅ Пройдено (≥70%)" if f_rate >= 70 else "❌ Не пройдено (<70%)"
    print(f"Критерий Faithfulness ≥ 70%: {status}")
    print("="*50)

if __name__ == "__main__":
    evaluate()