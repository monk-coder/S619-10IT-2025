from rag_pipeline import RAGPipeline

def main():
    print("=" * 50)
    print("RAG СИСТЕМА ПО ВАШИМ PDF")
    print("exit - выход")
    print("=" * 50)
    
    print("\nЗагрузка...")
    pipeline = RAGPipeline()
    print("Готово!\n")
    
    while True:
        question = input("Вопрос: ").strip()
        if question.lower() in ["exit", "quit", "выход"]:
            break
        if not question:
            continue
        
        print("Ищу ответ...")
        answer, sources = pipeline.ask(question)
        
        print("\nОТВЕТ:")
        print(answer)
        print("\nИСТОЧНИКИ:")
        for i, doc in enumerate(sources, 1):
            print(f"{i}. {doc.metadata.get('source', '?')}, стр. {doc.metadata.get('page', '?')}")
        print("-" * 40)

if __name__ == "__main__":
    main()