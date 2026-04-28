from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
FAISS_INDEX_PATH = "faiss_index"
OLLAMA_MODEL = "llama3.2:1b"

class RAGPipeline:
    def __init__(self):
        print("Загрузка индекса...")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH, 
            self.embeddings, 
            allow_dangerous_deserialization=True
        )
        print("Индекс загружен")
        
        self.llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0)
        
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""Ты — ассистент. Отвечай, используя только контекст.
Если ответа нет в контексте, скажи "Не могу найти ответ".

Контекст:
{context}

Вопрос: {question}

Ответ:"""
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": self.prompt_template},
            return_source_documents=True
        )
    
    def ask(self, question):
        result = self.qa_chain.invoke({"query": question})
        return result["result"], result["source_documents"]