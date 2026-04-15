"""
Тест-кейсы для ReAct Agent.
Запуск: python evaluate.py
"""
import time
from agent import ReActAgent

TEST_CASES = [
    {
        "id": 1,
        "query": "Какая погода в Москве завтра?",
        "expected_contains": ["°C", "Москва"],
        "expected_tool": "get_weather",
        "description": "Проверка получения погоды"
    },
    {
        "id": 2,
        "query": "Сколько будет 15% от 250000 рублей?",
        "expected_contains": ["37500"],
        "expected_tool": "calculator",
        "description": "Проверка математических вычислений"
    },
    {
        "id": 3,
        "query": "Найди информацию про архитектуру Transformer",
        "expected_contains": ["Transformer", "внимание"],
        "expected_tool": "web_search",
        "description": "Проверка веб-поиска"
    },
    {
        "id": 4,
        "query": "Переведи 5000 рублей в евро (текущий курс)",
        "expected_contains": ["евро", "EUR"],
        "expected_tools": ["web_search", "calculator"],
        "description": "Многошаговая задача: поиск + вычисление"
    },
    {
        "id": 5,
        "query": "Что такое RAG в контексте LLM?",
        "expected_contains": ["RAG", "Retrieval", "генерация"],
        "expected_tool": "web_search",
        "description": "Поиск определения термина"
    }
]

def evaluate_case(agent: ReActAgent, case: dict) -> dict:
    """Оценивает один тест-кейс."""
    print(f"\n{'='*60}")
    print(f"🧪 Тест #{case['id']}: {case['description']}")
    print(f"📝 Запрос: {case['query']}")
    print(f"{'-'*60}")
    
    start = time.time()
    result = agent.run(case['query'])
    duration = time.time() - start
    
    answer = result['answer'].lower()
    trace_text = "\n".join(result['trace']).lower()
    
    # Критерии успеха
    passed = True
    issues = []
    
    # 1. Проверка содержания ответа
    for expected in case.get('expected_contains', []):
        if expected.lower() not in answer and expected.lower() not in trace_text:
            passed = False
            issues.append(f"❌ Не найдено: '{expected}'")
    
    # 2. Проверка использования инструментов
    expected_tools = case.get('expected_tools', [case.get('expected_tool')])
    expected_tools = [t for t in expected_tools if t]  # filter None
    if expected_tools:
        used_tools = [t for t in expected_tools if t.lower() in trace_text]
        if not used_tools:
            passed = False
            issues.append(f"❌ Не использованы ожидаемые инструменты: {expected_tools}")
    
    # 3. Проверка статуса
    if result['status'] not in ['success']:
        passed = False
        issues.append(f"❌ Статус: {result['status']}")
    
    # 4. Проверка на бесконечный цикл
    if result['iterations'] >= 10 and result['status'] == 'max_iterations':
        passed = False
        issues.append("❌ Достигнут лимит итераций")
    
    # Вывод результатов
    print(f"\n⏱️  Время: {duration:.1f} сек")
    print(f"🔄 Итераций: {result['iterations']}")
    print(f"✅ Ответ: {result['answer'][:200]}{'...' if len(result['answer']) > 200 else ''}")
    
    if passed:
        print(f"\n🟢 ТЕСТ ПРОЙДЕН")
    else:
        print(f"\n🔴 ТЕСТ НЕ ПРОЙДЕН:")
        for issue in issues:
            print(f"   {issue}")
    
    return {
        "case_id": case['id'],
        "passed": passed,
        "duration": duration,
        "iterations": result['iterations'],
        "status": result['status'],
        "issues": issues
    }

def main():
    print("🚀 Запуск оценки ReAct Agent")
    print(f"📊 Тест-кейсов: {len(TEST_CASES)}")
    
    agent = ReActAgent(verbose=False)  # Отключаем подробный лог для чистоты отчёта
    
    results = []
    for case in TEST_CASES:
        result = evaluate_case(agent, case)
        results.append(result)
        time.sleep(2)  # Пауза между запросами
    
    # Итоговая статистика
    print(f"\n{'='*60}")
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    success_rate = passed / total * 100
    
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    print(f"⏱️  Среднее время: {sum(r['duration'] for r in results)/total:.1f} сек")
    print(f"🔄 Среднее итераций: {sum(r['iterations'] for r in results)/total:.1f}")
    
    if success_rate >= 80:
        print(f"\n🎉 КРИТЕРИЙ ВЫПОЛНЕН: ≥80% успеха!")
    else:
        print(f"\n⚠️  КРИТЕРИЙ НЕ ВЫПОЛНЕН: нужно ≥80%, получено {success_rate:.1f}%")
    
    # Детали по проваленным тестам
    failed = [r for r in results if not r['passed']]
    if failed:
        print(f"\n🔴 Проваленные тесты:")
        for r in failed:
            print(f"   #{r['case_id']}: {r['issues']}")
    
    return success_rate >= 80

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
