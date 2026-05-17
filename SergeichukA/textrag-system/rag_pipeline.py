"""
RAG Pipeline: модуль настройки и запуска конвейера Retrieval-Augmented Generation.
Оптимизирован для работы с локальными LLM и мультиязычным контекстом.
"""
import os
from typing import Tuple

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaLLM


# === Конфигурация ===
CONFIG = {
    "faiss_index_path": "faiss_index",
    "llm_model": "llama3.2",
    "embedding_model": "all-MiniLM-L6-v2",
    "llm_temperature": 0.3,
    "llm_timeout_seconds": 180,
    "llm_max_tokens": 512,
    "retrieval_top_k": 3,
}


def format_documents_with_metadata(documents: list) -> str:
    """
    Форматирует список документов в строку с указанием источника и страницы.
    
    Args:
        documents: Список объектов документов.
    
    Returns:
        Отформатированная строка с контекстом.
    """
    formatted = []
    for doc in documents:
        source = doc.metadata.get("source_file", "?")
        page = doc.metadata.get("page", "?")
        formatted.append(f"[{source}, стр. {page}]\n{doc.page_content}")
    return "\n\n".join(formatted)


def create_prompt_template() -> PromptTemplate:
    """
    Создаёт промпт для LLM с инструкциями для работы в мультиязычном режиме.
    
    Returns:
        Настроенный шаблон промпта.
    """
    return PromptTemplate.from_template(
        "Ты помогаешь отвечать на вопросы по документам. "
        "Контекст может быть на английском, вопрос — на русском.\n"
        "1. Внимательно прочитай контекст.\n"
        "2. Если в контексте есть информация по вопросу — кратко изложи её на русском.\n"
        "3. Если информации мало — дай лучший возможный ответ на основе того, что есть.\n"
        "4. Не придумывай факты, но и не отказывайся отвечать без крайней необходимости.\n"
        "5. Отвечай чётко, 2-4 предложения.\n\n"
        "Контекст:\n{context}\n\n"
        "Вопрос: {question}\n\n"
        "Ответ на русском:"
    )


def initialize_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    """Инициализирует модель эмбеддингов."""
    return HuggingFaceEmbeddings(model_name=model_name)


def load_vector_store(index_path: str, embeddings) -> FAISS:
    """Загружает сохранённый векторный индекс FAISS."""
    return FAISS.load_local(
        index_path,
        embeddings,
        allow_dangerous_deserialization=True
    )


def initialize_llm(model: str, temperature: float, timeout: int, max_tokens: int) -> OllamaLLM:
    """Инициализирует локальную LLM через Ollama."""
    return OllamaLLM(
        model=model,
        temperature=temperature,
        request_timeout=timeout,
        num_predict=max_tokens,
    )


def build_rag_chain(retriever, llm, prompt: PromptTemplate):
    """
    Собирает исполняемый конвейер RAG из компонентов.
    
    Returns:
        Готовая к выполнению цепочка (chain).
    """
    return (
        {
            "context": retriever | format_documents_with_metadata,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )


def setup_rag_pipeline() -> Tuple:
    """
    Основная функция настройки RAG-пайплайна.
    
    Returns:
        Кортеж (chain, vector_db) для дальнейшего использования.
    
    Raises:
        FileNotFoundError: Если индекс FAISS не найден.
    """
    index_path = CONFIG["faiss_index_path"]
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"Индекс не найден по пути '{index_path}'. "
            "Сначала запустите data_preprocessing.py"
        )
    
    # Инициализация компонентов
    embeddings = initialize_embeddings(CONFIG["embedding_model"])
    vector_db = load_vector_store(index_path, embeddings)
    retriever = vector_db.as_retriever(
        search_kwargs={"k": CONFIG["retrieval_top_k"]}
    )
    
    llm = initialize_llm(
        model=CONFIG["llm_model"],
        temperature=CONFIG["llm_temperature"],
        timeout=CONFIG["llm_timeout_seconds"],
        max_tokens=CONFIG["llm_max_tokens"],
    )
    
    prompt = create_prompt_template()
    chain = build_rag_chain(retriever, llm, prompt)
    
    return chain, vector_db


# Тестовый запуск модуля
if __name__ == "__main__":
    chain, _ = setup_rag_pipeline()
    test_question = "Что такое causal mask?"
    print(f"Вопрос: {test_question}")
    print(f"Ответ: {chain.invoke(test_question)}")