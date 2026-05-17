"""
Модуль оценки качества ответов RAG-системы.
Измеряет Faithfulness и Relevance по ручным меткам.
"""
from typing import List, Dict
from rag_pipeline import setup_rag_pipeline


# === Конфигурация тестовых вопросов ===
TEST_QUESTIONS: List[str] = [
    "Что такое causal mask в Transformer?",
    "Как работает механизм self-attention?",
    "В чем разница между fine-tuning и prompt engineering?",
    "Какие архитектуры нейросетей обсуждаются в лекциях?",
    "Как оценивается качество эмбеддингов?",
    "Что такое hallucination в LLM?",
    "Какие методы регуляризации упоминаются?",
    "Как работает backpropagation?",
    "Что такое zero-shot классификация?",
    "Какие ограничения есть у FAISS индексации?",
]

EVALUATION_METRICS = {
    "faithfulness": "Ответ строго следует контексту?",
    "relevance": "Найденные чанки релевантны вопросу?",
}

THRESHOLD_PASS: float = 70.0  # Минимальный процент для прохождения оценки


def get_manual_rating(metric_name: str, description: str) -> int:
    """
    Запрашивает у пользователя ручную оценку по метрике.
    
    Returns:
        0 или 1 в зависимости от выбора пользователя.
    """
    while True:
        try:
            rating = int(input(f"{metric_name} ({description}) [0/1]: "))
            if rating in (0, 1):
                return rating
            print("⚠️ Введите 0 или 1.")
        except ValueError:
            print("⚠️ Некорректный ввод. Попробуйте снова.")


def evaluate_single_question(
    question: str,
    chain,
    retriever,
    question_number: int
) -> Dict[str, int]:
    """
    Оценивает ответ на один вопрос.
    
    Returns:
        Словарь с оценками по метрикам.
    """
    print(f"\n🔹 Вопрос {question_number}: {question}")
    
    # Получение и отображение источников
    documents = retriever.invoke(question)
    print("📎 Источники:")
    for doc in documents:
        source = doc.metadata.get("source_file", "?")
        page = doc.metadata.get("page", "?")
        print(f" - {source} стр. {page}")
    
    # Генерация ответа
    answer = chain.invoke(question)
    print(f"💬 Ответ: {answer}")
    
    # Сбор ручных оценок
    ratings = {}
    for metric, desc in EVALUATION_METRICS.items():
        ratings[metric] = get_manual_rating(metric.capitalize(), desc)
    
    print("✅ Оценено.")
    return ratings


def calculate_metrics(results: List[Dict[str, int]]) -> Dict[str, float]:
    """
    Вычисляет средние значения по всем оценкам.
    
    Returns:
        Словарь с процентными значениями метрик.
    """
    if not results:
        return {}
    
    metrics = {}
    for metric_name in EVALUATION_METRICS:
        total = sum(r[metric_name] for r in results)
        metrics[metric_name] = (total / len(results)) * 100
    return metrics


def display_results(metrics: Dict[str, float]) -> None:
    """Выводит итоговые результаты оценки."""
    print("\n" + "=" * 50)
    print("📈 ИТОГИ ОЦЕНКИ")
    
    for metric, value in metrics.items():
        print(f"{metric.capitalize()} Rate: {value:.1f}%")
    
    # Проверка порога прохождения по Faithfulness
    faithfulness = metrics.get("faithfulness", 0)
    status = "✅ Пройдено" if faithfulness >= THRESHOLD_PASS else "❌ Не пройдено"
    print(f"Критерий Faithfulness ≥ {THRESHOLD_PASS}%: {status}")
    print("=" * 50)


def run_evaluation() -> None:
    """Основная функция запуска оценки системы."""
    print("📊 Загрузка системы для оценки...")
    chain, vector_db = setup_rag_pipeline()
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    
    print("\n" + "=" * 50)
    print("ОЦЕНКА КАЧЕСТВА ОТВЕТОВ")
    for metric, desc in EVALUATION_METRICS.items():
        print(f"{metric.capitalize()} (0/1): {desc}")
    print("=" * 50)
    
    # Оценка каждого вопроса
    all_results = []
    for idx, question in enumerate(TEST_QUESTIONS, start=1):
        result = evaluate_single_question(question, chain, retriever, idx)
        all_results.append(result)
    
    # Подсчёт и отображение результатов
    final_metrics = calculate_metrics(all_results)
    display_results(final_metrics)


if __name__ == "__main__":
    run_evaluation()