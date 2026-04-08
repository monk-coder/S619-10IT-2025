import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def process_documents(docs_dir="docs", index_dir="faiss_index"):
    if not os.path.exists(docs_dir):
        print(f"⚠️ Папка '{docs_dir}' не найдена. Проверяю корень...")
        pdf_files = glob.glob("*.pdf")
        if pdf_files:
            docs_dir = "."
            print(f"✅ PDF найдены в корне.")
        else:
            raise FileNotFoundError("❌ PDF не найдены. Положите их в 'docs/' или в корень.")
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

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"📦 Получено {len(chunks)} фрагментов.")

    print("🧠 Инициализация эмбеддингов (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("🔍 Построение FAISS индекса...")
    db = FAISS.from_documents(chunks, embeddings)

    os.makedirs(index_dir, exist_ok=True)
    db.save_local(index_dir)
    print(f"💾 Индекс сохранён в '{index_dir}/'")
    print("✅ Готово! Запускай rag_qa.py или evaluate.py")

if __name__ == "__main__":
    process_documents()
