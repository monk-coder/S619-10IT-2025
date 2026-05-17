"""
Интерактивный CLI-интерфейс для RAG-системы.
Позволяет задавать вопросы и получать ответы с указанием источников.
"""
import sys
from typing import Optional


def display_sources(documents: list) -> None:
    """Выводит информацию об источниках для ответа."""
    print("\n📚 [Источники]")
    for doc in documents:
        source = doc.metadata.get("source_file", "?")
        page = doc.metadata.get("page", "?")
        print(f" • {source}, стр. {page}")


def get_user_input(prompt: str = "> Вопрос: ") -> Optional[str]:
    """
    Получает ввод от пользователя.
    
    Returns:
        Введённая строка или None при сигнале выхода.
    """
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        return None


def is_exit_command(text: str) -> bool:
    """Проверяет, является ли ввод командой выхода."""
    exit_commands = {"exit", "quit", "выход", "вых"}
    return text.lower() in exit_commands


def run_interactive_session() -> None:
    """Запускает интерактивный диалог с пользователем."""
    print("🚀 Загрузка RAG-системы...")
    
    try:
        from rag_pipeline import setup_rag_pipeline
        chain, vector_db = setup_rag_pipeline()
    except Exception as initialization_error:
        print(f"❌ Ошибка инициализации: {initialization_error}")
        sys.exit(1)
    
    print("\n=== 🤖 RAG QA System ===")
    print("Введите вопрос или 'exit' для выхода.\n")
    
    while True:
        question = get_user_input()
        
        if question is None or is_exit_command(question):
            print("👋 До свидания!")
            break
        
        if not question:
            continue
        
        try:
            # Получение релевантных документов
            retriever = vector_db.as_retriever(
                search_kwargs={"k": 3}
            )
            documents = retriever.invoke(question)
            
            # Отображение источников
            display_sources(documents)
            
            # Генерация и вывод ответа
            print("\n💡 [Генерация...]")
            answer = chain.invoke(question)
            print(f"Ответ: {answer}\n{'─' * 50}")
            
        except KeyboardInterrupt:
            print("\n👋 Выход.")
            break
        except Exception as error:
            print(f"⚠️ Ошибка: {error}")


if __name__ == "__main__":
    run_interactive_session()