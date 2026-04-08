import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def process_documents(docs_dir="docs", index_dir="faiss_index"):
    print("📄 Загрузка PDF документов...")
    pdf_files = glob.glob(os.path.join(docs_dir, "*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"В папке {docs_dir} не найдено PDF файлов.")

    docs = []
    for pdf_path in pdf_files:
        loader = PyPDFLoader(pdf_path)
        docs.extend(loader.load())
    print(f"✅ Загружено {len(docs)} страниц из {len(pdf_files)} файлов.")

    # Примечание: LangChain по умолчанию считает chunk_size в символах.
    # 500 символов ≈ 100-150 токенов. Для ~500 токенов обычно ставят chunk_size=2000.
    # Оставляем 500, как в ТЗ. При необходимости увеличьте до 2000.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"✂️ Получено {len(chunks)} фрагментов (chunks).")

    print("🧠 Инициализация эмбеддингов (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("📦 Построение FAISS индекса...")
    db = FAISS.from_documents(chunks, embeddings)

    os.makedirs(index_dir, exist_ok=True)
    db.save_local(index_dir)
    print(f"💾 Индекс успешно сохранён в {index_dir}/")

if __name__ == "__main__":
    process_documents()
