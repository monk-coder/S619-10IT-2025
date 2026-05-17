"""
RAG Pipeline: retrieval + LLM generation
Исправленная версия для малых моделей + мультиязычный контекст
"""
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

FAISS_DIR = "faiss_index"
LLM_MODEL = "llama3.2"  # ← без :1b, как в ollama list
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def setup_rag_pipeline():
    if not os.path.exists(FAISS_DIR):
        raise FileNotFoundError("Индекс не найден. Сначала запустите data_preprocessing.py")

    # Загрузка эмбеддингов и векторной БД
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 3})
    
    # LLM с более мягкими настройками для малых моделей
    llm = OllamaLLM(
        model=LLM_MODEL, 
        temperature=0.3,        # ← чуть выше для креативности
        request_timeout=180,    # ← больше времени на генерацию
        num_predict=512         # ← достаточно для развёрнутого ответа
    )

    # 🔥 КЛЮЧЕВОЕ: мягкий промпт, который работает с малыми моделями
    prompt = PromptTemplate.from_template(
        "Ты помогаешь отвечать на вопросы по документам. Контекст может быть на английском, вопрос — на русском.\n"
        "1. Внимательно прочитай контекст.\n"
        "2. Если в контексте есть информация по вопросу — кратко изложи её на русском.\n"
        "3. Если информации мало — дай лучший возможный ответ на основе того, что есть.\n"
        "4. Не придумывай факты, но и не отказывайся отвечать без крайней необходимости.\n"
        "5. Отвечай чётко, 2-4 предложения.\n\n"
        "Контекст:\n{context}\n\n"
        "Вопрос: {question}\n\n"
        "Ответ на русском:"
    )

    # Сборка цепочки
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, db

def format_docs(docs):
    """Форматирует документы с указанием источника и страницы."""
    return "\n\n".join(
        f"[{d.metadata.get('source_file', '?')}, стр. {d.metadata.get('page', '?')}]\n{d.page_content}"
        for d in docs
    )

# Тестовый запуск
if __name__ == "__main__":
    chain, db = setup_rag_pipeline()
    print(chain.invoke("Что такое causal mask?"))