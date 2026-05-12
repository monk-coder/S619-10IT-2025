# evaluate.py
# Скрипт для оценки качества RAG-системы на 10 тест-вопросах

from rag_pipeline import load_vectorstore, ask, format_sources


# 10 тестовых вопросов — замените на вопросы по вашим PDF
TEST_QUESTIONS = [
    "Когда пишется суффикс -ИНК-, а когда -ЕНК-?",
    "Как определить суффикс -ИЦ- или -ЕЦ- в существительных?",
    "Когда наречие пишется с суффиксом -О, а когда с -А?",
    "Как выделяются деепричастные обороты на письме?",
    "Когда запятая не ставится между однородными деепричастными оборотами?",
]


def evaluate():
    """Запускает RAG на 10 вопросах и считает Faithfulness и Relevance."""
    print("=" * 60)
    print("  Оценка RAG-системы")
    print("=" * 60)
    print("Для каждого ответа вы оцениваете вручную:")
    print("  Faithfulness (F): ответ основан на источниках? (1 = да, 0 = нет)")
    print("  Relevance    (R): источники релевантны вопросу? (1 = да, 0 = нет)")
    print()

    # Загружаем индекс
    try:
        vectorstore = load_vectorstore()
    except FileNotFoundError as e:
        print(f"[!] {e}")
        return

    # Списки оценок
    faithfulness_scores = []
    relevance_scores = []

    for i, question in enumerate(TEST_QUESTIONS, start=1):
        print(f"\n{'=' * 60}")
        print(f"Вопрос {i}/{len(TEST_QUESTIONS)}: {question}")
        print("=" * 60)

        # Получаем ответ
        answer, chunks = ask(vectorstore, question)

        # Выводим источники и ответ
        print()
        print(format_sources(chunks))
        print(f"\nОтвет: {answer}")

        # Просим пользователя оценить вручную
        print()
        f_score = _get_score("Faithfulness (ответ основан на источниках?)")
        r_score = _get_score("Relevance    (источники релевантны вопросу?)")

        faithfulness_scores.append(f_score)
        relevance_scores.append(r_score)

        print(f"[+] Оценки сохранены: F={f_score}, R={r_score}")

    # Итоговый отчёт
    _print_report(faithfulness_scores, relevance_scores)


def _get_score(label):
    """Запрашивает оценку 0 или 1 у пользователя."""
    while True:
        raw = input(f"  {label} [0/1]: ").strip()
        if raw in ("0", "1"):
            return int(raw)
        print("  [!] Введите 0 или 1")


def _print_report(faithfulness_scores, relevance_scores):
    """Выводит итоговый отчёт по оценке."""
    n = len(faithfulness_scores)

    faithfulness_rate = sum(faithfulness_scores) / n * 100
    relevance_rate = sum(relevance_scores) / n * 100

    print("\n" + "=" * 60)
    print("  ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 60)
    print(f"  Всего вопросов:    {n}")
    print(f"  Faithfulness rate: {faithfulness_rate:.0f}%  "
          f"({sum(faithfulness_scores)}/{n} ответов основаны на источниках)")
    print(f"  Relevance rate:    {relevance_rate:.0f}%  "
          f"({sum(relevance_scores)}/{n} источников релевантны)")

    # Подробная таблица
    print("\n  Детальные оценки:")
    print(f"  {'№':<4} {'Faithfulness':<15} {'Relevance'}")
    print(f"  {'-'*4} {'-'*15} {'-'*10}")
    for i, (f, r) in enumerate(zip(faithfulness_scores, relevance_scores), start=1):
        print(f"  {i:<4} {f:<15} {r}")

    print("=" * 60)

    # Проверяем минимальный критерий
    if faithfulness_rate >= 70:
        print("  [OK] Faithfulness rate >= 70% — минимальный критерий выполнен!")
    else:
        print("  [!] Faithfulness rate < 70% — нужно улучшить систему.")

    print("=" * 60)


if __name__ == "__main__":
    evaluate()