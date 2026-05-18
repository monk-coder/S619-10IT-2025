# data_preprocessing.py
# Скрипт для загрузки PDF, разбивки на чанки и создания FAISS индекса

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# Папка с PDF-файлами
DOCS_DIR = "docs"
# Папка для сохранения FAISS индекса
INDEX_DIR = "faiss_index"
# Модель для эмбеддингов
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Размер чанка в символах (примерно 500 токенов)
CHUNK_SIZE = 2000
# Перекрытие между чанками (примерно 50 токенов)
CHUNK_OVERLAP = 200


def load_pdfs(docs_dir):
    """Загружает все PDF из папки и возвращает список документов."""
    all_docs = []

    # Получаем список PDF файлов
    pdf_files = [f for f in os.listdir(docs_dir) if f.endswith(".pdf")]

    if not pdf_files:
        print(f"[!] В папке '{docs_dir}' не найдено PDF файлов.")
        print("[!] Положите PDF файлы в папку docs/ и запустите скрипт снова.")
        return []

    print(f"[+] Найдено PDF файлов: {len(pdf_files)}")

    for pdf_file in pdf_files:
        pdf_path = os.path.join(docs_dir, pdf_file)
        print(f"    Загружаю: {pdf_file}")

        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            all_docs.extend(docs)
            print(f"    Загружено страниц: {len(docs)}")
        except Exception as e:
            print(f"    [!] Ошибка при загрузке {pdf_file}: {e}")

    print(f"\n[+] Итого загружено страниц: {len(all_docs)}")
    return all_docs


def split_into_chunks(docs):
    """Разбивает документы на чанки по 500 токенов с overlap 50 токенов."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # Разделители: сначала пробуем абзацы, потом строки, потом слова
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = splitter.split_documents(docs)
    print(f"[+] Итого чанков после разбивки: {len(chunks)}")
    return chunks


def create_faiss_index(chunks):
    """Создаёт FAISS индекс из чанков с помощью sentence-transformers."""
    print(f"\n[+] Загружаю модель эмбеддингов: {EMBEDDING_MODEL}")
    print("    (первый запуск может занять время — модель скачивается)")

    # Загружаем модель эмбеддингов локально
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )

    print("[+] Создаю FAISS индекс...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    print(f"[+] Сохраняю индекс в папку '{INDEX_DIR}'...")
    os.makedirs(INDEX_DIR, exist_ok=True)
    vectorstore.save_local(INDEX_DIR)

    print(f"[+] Индекс успешно сохранён!")
    return vectorstore


def main():
    print("=" * 50)
    print("  Подготовка данных для RAG-системы")
    print("=" * 50)

    # Проверяем что папка docs существует
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"[!] Создана папка '{DOCS_DIR}'.")
        print("[!] Положите PDF файлы в папку docs/ и запустите скрипт снова.")
        return

    # Шаг 1: загружаем PDF
    print("\n[Шаг 1] Загрузка PDF файлов...")
    docs = load_pdfs(DOCS_DIR)

    if not docs:
        return

    # Шаг 2: разбиваем на чанки
    print("\n[Шаг 2] Разбивка на чанки...")
    chunks = split_into_chunks(docs)

    # Шаг 3: создаём FAISS индекс
    print("\n[Шаг 3] Создание FAISS индекса...")
    create_faiss_index(chunks)

    print("\n" + "=" * 50)
    print("  Готово! Теперь можно запустить: python rag_qa.py")
    print("=" * 50)


if __name__ == "__main__":
    main()