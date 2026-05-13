import sys
from rag_pipeline import setup_rag_pipeline

def main():
    print("🚀 Загрузка RAG-системы...")
    try:
        chain, db = setup_rag_pipeline()
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        sys.exit(1)

    print("\n=== 🤖 RAG QA System ===")
    print("Введите вопрос или 'exit' для выхода.\n")

    while True:
        try:
            q = input("> Вопрос: ").strip()
            if q.lower() in ["exit", "quit", "выход"]:
                print("👋 До свидания!")
                break
            if not q:
                continue

            # Извлекаем источники для красивого вывода
            docs = db.as_retriever(search_kwargs={"k": 3}).invoke(q)
            
            print("\n📚 [Источники]")
            for doc in docs:
                print(f"  • {doc.metadata.get('source_file', '?')}, стр. {doc.metadata.get('page', '?')}")

            print("\n💡 [Генерация...]")
            ans = chain.invoke(q)
            print(f"Ответ: {ans}\n{'─' * 50}")
            
        except KeyboardInterrupt:
            print("\n👋 Выход.")
            break
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")

if __name__ == "__main__":
    main()
