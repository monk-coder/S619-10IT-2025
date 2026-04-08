# 🧠 RAG-система (LangChain + FAISS + Ollama)

## 🚀 Быстрый старт
1. Установи Ollama: https://ollama.com
2. Скачай модель: `ollama pull llama3.2:1b`
3. Установи зависимости: `pip install -r requirements.txt`
4. Скачай PDF: `python download_pdfs.py`
5. Создай индекс: `python data_preprocessing.py`
6. Запусти: `python rag_qa.py`

## 📁 Структура
- `docs/` — PDF-документы (скачиваются автоматически)
- `faiss_index/` — векторный индекс (создаётся автоматически)
- `*.py` — исходный код системы

## 📊 Результаты оценки
- Faithfulness: ___%
- Relevance: ___%
(заполни после запуска evaluate.py)
