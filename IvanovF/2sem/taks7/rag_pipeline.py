# rag_pipeline.py
# Модуль для поиска релевантных чанков и генерации ответа через Ollama

import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import ollama


# Настройки
INDEX_DIR = "faiss_index"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "llama3.2:1b"
# Сколько чанков брать для контекста
TOP_K = 3


def load_vectorstore():
    """Загружает FAISS индекс с диска."""
    if not os.path.exists(INDEX_DIR):
        raise FileNotFoundError(
            f"Папка '{INDEX_DIR}' не найдена. "
            "Сначала запустите: python data_preprocessing.py"
        )

    print("[+] Загружаю FAISS индекс...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )

    vectorstore = FAISS.load_local(
        INDEX_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )

    print("[+] Индекс загружен!")
    return vectorstore


def search_relevant_chunks(vectorstore, question):
    """Ищет top-K самых похожих чанков по вопросу пользователя."""
    results = vectorstore.similarity_search(question, k=TOP_K)
    return results


def build_prompt(context_chunks, question):
    """Собирает промпт из контекста и вопроса."""
    # Объединяем все чанки в один текст контекста
    context_text = "\n\n---\n\n".join([chunk.page_content for chunk in context_chunks])

    prompt = f"""Ты — помощник, который отвечает на вопросы строго на основе предоставленного контекста.
Если ответ не найден в контексте — так и скажи, не придумывай.

Контекст:
{context_text}

Вопрос: {question}

Ответ:"""

    return prompt


def generate_answer(prompt):
    """Отправляет промпт в Ollama и получает ответ."""
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"[Ошибка при обращении к Ollama]: {e}\nПроверьте, что Ollama запущена и модель загружена: ollama pull {LLM_MODEL}"


def format_sources(chunks):
    """Форматирует список источников для вывода пользователю."""
    sources = []
    for i, chunk in enumerate(chunks, start=1):
        # Получаем метаданные чанка
        source = chunk.metadata.get("source", "неизвестный файл")
        page = chunk.metadata.get("page", "?")

        # Берём только имя файла без пути
        filename = os.path.basename(source)

        sources.append(f"[Источник {i}]: {filename}, стр. {page + 1}")

    return "\n".join(sources)


def ask(vectorstore, question):
    """
    Полный RAG-пайплайн:
    1. Поиск релевантных чанков
    2. Построение промпта
    3. Генерация ответа
    4. Возврат ответа и источников
    """
    # Шаг 1: ищем похожие чанки
    chunks = search_relevant_chunks(vectorstore, question)

    # Шаг 2: строим промпт
    prompt = build_prompt(chunks, question)

    # Шаг 3: генерируем ответ
    answer = generate_answer(prompt)

    return answer, chunks