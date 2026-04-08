import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def process_documents(docs_dir="docs", index_dir="faiss_index"):
    # 🔍 Автопоиск PDF: сначала в docs/, потом в корне
    if not os.path.exists(docs_dir):
        print(f"⚠️ Папка '{docs_dir}' не найдена. Проверяю корень проекта...")
        pdf_files = glob.glob("*.pdf")
        if pdf_files:
            docs_dir = "."
            print(f"✅ PDF найдены в корне.")
        else:
            raise FileNotFoundError("❌ PDF не найдены. Положите их в папку 'docs/' или в корень проекта.")
    else:
        pdf_files = glob.glob(os.path.join(docs_dir, "*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"❌ В '{docs_dir}' нет PDF файлов.")

    print(f"📄 Загрузка {len(pdf_files)} документов из '{docs_dir}'...")
    docs = []
    for pdf_path in pdf_files:
        loader = PyPDFLoader(pdf_path)
        docs.extend(loader.load())
    print(f"✅ Загружено {len(docs)} страниц.")

    # ✂️ Chunking: 500 символов, overlap 50 (стандарт LangChain)
    # Примечание: LangChain считает в символах. 500 chars ≈ 120-150 токенов.
    # Для строгого подсчёта в токенах можно подключить tiktoken, но для учебных задач этого достаточно.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"📦 Получено {len(chunks)} фрагментов.")

    # 🧠 Embeddings
    print("🧠 Инициализация модели all-MiniLM-L6-v2 (первый запуск скачает ~80MB)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 📦 FAISS Index
    print("🔍 Построение векторного индекса FAISS...")
    db = FAISS.from_documents(chunks, embeddings)

    # 💾 Сохранение
    os.makedirs(index_dir, exist_ok=True)
    db.save_local(index_dir)
    print(f"💾 Индекс успешно сохранён в '{index_dir}/'")
    print("✅ Готово! Можно запускать rag_qa.py или evaluate.py")

if __name__ == "__main__":
    process_documents()
