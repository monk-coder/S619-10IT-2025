import os
import tiktoken
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DOCS_DIR = "docs"
FAISS_DIR = "faiss_index"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def token_length(text: str) -> int:
    """Считает точное количество токенов для строгого соответствия ТЗ."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def preprocess():
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"⚠️  Создайте папку '{DOCS_DIR}' и поместите туда 5-10 PDF файлов.")
        return

    print("📥 Загрузка PDF...")
    documents = []
    for fname in os.listdir(DOCS_DIR):
        if fname.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(DOCS_DIR, fname))
            pages = loader.load()
            for p in pages:
                p.metadata["source_file"] = fname
            documents.extend(pages)
    print(f"✅ Загружено {len(documents)} страниц.")

    print("✂️ Chunking: 500 токенов, overlap 50...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=token_length,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    print(f"✅ Создано {len(chunks)} фрагментов.")

    print("🧠 Генерация эмбеддингов и построение FAISS...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = FAISS.from_documents(chunks, embeddings)
    
    if not os.path.exists(FAISS_DIR):
        os.makedirs(FAISS_DIR)
    db.save_local(FAISS_DIR)
    print(f"💾 Индекс сохранён в '{FAISS_DIR}/'. Готово!")

if __name__ == "__main__":
    preprocess()