from rag_pipeline import load_rag_system, get_answer_and_sources

def main():
    print("🚀 Загрузка RAG системы...")
    rag_chain, retriever = load_rag_system()
    print("✅ Система готова. Введите вопрос или 'exit' для выхода.\n")

    while True:
        question = input("> Вопрос: ").strip()
        if question.lower() in ("exit", "выход", "quit"):
            print("👋 До свидания!")
            break
        if not question:
            continue
        try:
            answer, sources = get_answer_and_sources(rag_chain, retriever, question)
            for i, src in enumerate(sources, 1):
                print(f"[Источник {i}]: {src['source']}, стр. {src['page']}")
            print(f"\nОтвет: {answer}\n" + "="*50)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("💡 Проверь: Ollama запущена? Индекс создан?")

if __name__ == "__main__":
    main()
