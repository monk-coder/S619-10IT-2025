from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def load_rag_system(index_dir="faiss_index"):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 3})

    llm = ChatOllama(model="llama3.2:1b", temperature=0, base_url="http://localhost:11434")

    prompt = ChatPromptTemplate.from_template(
        "Используй контекст для ответа на вопрос: {context} / {question}"
    )

    def format_docs(docs):
        return "\n\n---\n\n".join([
            f"[Источник: {d.metadata.get('source', 'Неизвестно')}, стр. {d.metadata.get('page', 'N/A')}]\n{d.page_content}"
            for d in docs
        ])

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain, retriever

def get_answer_and_sources(rag_chain, retriever, question):
    docs = retriever.invoke(question)
    sources = [
        {"source": d.metadata.get("source", "Unknown"), "page": d.metadata.get("page", "N/A")}
        for d in docs
    ]
    answer = rag_chain.invoke(question)
    return answer, sources
