"""
Модуль предобработки данных для RAG-системы.
Загружает PDF-документы, разбивает на чанки и создаёт векторный индекс FAISS.
"""
import os
from pathlib import Path

import tiktoken
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter


# === Конфигурация ===
CONFIG = {
    "docs_directory": "docs",
    "faiss_index_directory": "faiss_index",
    "embedding_model": "all-MiniLM-L6-v2",
    "chunk_size_tokens": 500,
    "chunk_overlap_tokens": 50,
    "encoding_name": "cl100k_base",  # Токенизатор для точного подсчёта
}


def count_tokens(text: str, encoding_name: str = CONFIG["encoding_name"]) -> int:
    """
    Подсчитывает количество токенов в тексте с использованием указанного кодировщика.
    
    Args:
        text: Исходный текст.
        encoding_name: Название кодировки tiktoken.
    
    Returns:
        Количество токенов в тексте.
    """
    encoder = tiktoken.get_encoding(encoding_name)
    return len(encoder.encode(text))


def load_pdf_documents(directory: str) -> list:
    """
    Загружает все PDF-файлы из указанной директории.
    
    Args:
        directory: Путь к папке с документами.
    
    Returns:
        Список объектов документов с метаданными.
    """
    documents = []
    pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]
    
    for filename in pdf_files:
        file_path = os.path.join(directory, filename)
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        for page in pages:
            page.metadata["source_file"] = filename
            documents.append(page)
    
    return documents


def split_into_chunks(documents: list, chunk_size: int, chunk_overlap: int) -> list:
    """
    Разбивает документы на текстовые чанки с заданными параметрами.
    
    Args:
        documents: Список документов для разбиения.
        chunk_size: Максимальный размер чанка в токенах.
        chunk_overlap: Перекрытие между соседними чанками.
    
    Returns:
        Список чанков (документов меньшего размера).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=count_tokens,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(documents)


def create_vector_index(documents: list, model_name: str, save_path: str) -> None:
    """
    Создаёт и сохраняет векторный индекс FAISS на основе документов.
    
    Args:
        documents: Список документов для индексации.
        model_name: Название модели эмбеддингов.
        save_path: Путь для сохранения индекса.
    """
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    vector_store = FAISS.from_documents(documents, embeddings)
    
    os.makedirs(save_path, exist_ok=True)
    vector_store.save_local(save_path)


def preprocess_data() -> None:
    """Основная функция предобработки: загрузка → чанкинг → индексация."""
    docs_dir = CONFIG["docs_directory"]
    
    # Проверка наличия директории с документами
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        print(f"⚠️ Создайте папку '{docs_dir}' и поместите туда 5-10 PDF-файлов.")
        return
    
    # Шаг 1: Загрузка документов
    print("📥 Загрузка PDF-документов...")
    documents = load_pdf_documents(docs_dir)
    print(f"✅ Загружено страниц: {len(documents)}")
    
    # Шаг 2: Разбиение на чанки
    print(f"✂️ Чанкинг: {CONFIG['chunk_size_tokens']} токенов, overlap {CONFIG['chunk_overlap_tokens']}...")
    chunks = split_into_chunks(
        documents,
        CONFIG["chunk_size_tokens"],
        CONFIG["chunk_overlap_tokens"]
    )
    print(f"✅ Создано чанков: {len(chunks)}")
    
    # Шаг 3: Создание векторного индекса
    print("🧠 Генерация эмбеддингов и построение индекса FAISS...")
    create_vector_index(
        chunks,
        CONFIG["embedding_model"],
        CONFIG["faiss_index_directory"]
    )
    print(f"💾 Индекс сохранён в '{CONFIG['faiss_index_directory']}/'. Готово!")


if __name__ == "__main__":
    preprocess_data()