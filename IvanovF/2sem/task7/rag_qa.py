# rag_qa.py
# Основной скрипт — интерактивный чат с RAG-системой

from rag_pipeline import load_vectorstore, ask, format_sources


def main():
    print("=" * 50)
    print("  RAG-система для вопросов по документам")
    print("=" * 50)
    print("Введите 'выход' или 'exit' чтобы завершить.\n")

    # Загружаем индекс один раз при старте
    try:
        vectorstore = load_vectorstore()
    except FileNotFoundError as e:
        print(f"[!] {e}")
        return

    print("\nСистема готова! Задавайте вопросы.\n")

    while True:
        # Получаем вопрос от пользователя
        try:
            question = input("> Вопрос: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[+] Выход из программы.")
            break

        # Проверяем команду выхода
        if question.lower() in ("выход", "exit", "quit", ""):
            print("[+] Выход из программы.")
            break

        print("\n[+] Ищу релевантные фрагменты...")

        # Запускаем RAG-пайплайн
        answer, chunks = ask(vectorstore, question)

        # Выводим источники
        print()
        print(format_sources(chunks))

        # Выводим ответ
        print(f"\nОтвет: {answer}")
        print("\n" + "-" * 50 + "\n")


if __name__ == "__main__":
    main()