import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

PDF_DIRECTORY = "docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
FAISS_INDEX_PATH = "faiss_index"

def load_documents_from_directory(directory):
    all_documents = []
    for file in os.listdir(directory):
        if file.endswith(".pdf"):
            file_path = os.path.join(directory, file)
            print(f"Загружаю: {file}")
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            for doc in documents:
                doc.metadata["source"] = file
            all_documents.extend(documents)
    return all_documents

def split_documents(documents, chunk_size, chunk_overlap):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Создано {len(chunks)} чанков")
    return chunks

def create_faiss_index(chunks, embedding_model_name, save_path):
    print("Создаю эмбеддинги...")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(save_path)
    print(f"Сохранено в {save_path}")
    return vectorstore

if __name__ == "__main__":
    print("=== ОБРАБОТКА PDF ===\n")
    documents = load_documents_from_directory(PDF_DIRECTORY)
    print(f"Загружено {len(documents)} страниц")
    chunks = split_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP)
    create_faiss_index(chunks, EMBEDDING_MODEL, FAISS_INDEX_PATH)
    print("=== ГОТОВО ===")
