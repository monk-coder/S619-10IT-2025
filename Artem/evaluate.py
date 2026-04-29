"""
Автоматическая оценка агента на 5 тест-кейсах.
"""
import time
import json
from agent import ReActAgent


# Тест-кейсы
TEST_CASES = [
    {
        "id": 1,
        "question": "Какая погода в Москве завтра?",
        "expected_tools": ["get_weather"],
        "check": lambda answer: "°C" in answer or "градус" in answer.lower() or "погода" in answer.lower()
    },
    {
        "id": 2,
        "question": "Сколько будет 15% от 250000 рублей?",
        "expected_tools": ["calculator"],
        "check": lambda answer: "37500" in answer
    },
    {
        "id": 3,
        "question": "Найди информацию про архитектуру Transformer",
        "expected_tools": ["web_search"],
        "check": lambda answer: len(answer) > 50 and ("attention" in answer.lower() or "transformer" in answer.lower())
    },
    {
        "id": 4,
        "question": "Переведи 5000 рублей в евро (текущий курс)",
        "expected_tools": ["web_search", "calculator"],
        "check": lambda answer: "€" in answer or "евро" in answer.lower() or any(c.isdigit() for c in answer)
    },
    {
        "id": 5,
        "question": "Что такое RAG в контексте LLM?",
        "expected_tools": ["web_search"],
        "check": lambda answer: "rag" in answer.lower() or "retrieval" in answer.lower() or "поиск" in answer.lower()
    }
]


def evaluate_agent(agent: ReActAgent, test_cases: list) -> dict:
    """Запускает оценку агента."""
    results = []
    passed = 0
    
    print(f"\n{'='*70}")
    print(f"🧪 Запуск оценки: {len(test_cases)} тест-кейсов")
    print(f"{'='*70}\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Тест #{test['id']}: {test['question'][:60]}...")
        print("-" * 70)
        
        start_time = time.time()
        result = agent.run(test["question"])
        elapsed = time.time() - start_time
        
        # Проверка результата
        answer = result.get("answer", "") or ""
        is_correct = test["check"](answer) if answer else False
        
        # Проверка использованных инструментов
        used_tools = [step.get("tool") for step in result.get("trace", []) if step.get("step") == "action"]
        tools_match = any(et in used_tools for et in test["expected_tools"]) if test["expected_tools"] else True
        
        status = "✅ PASS" if (is_correct and tools_match and result["success"]) else "❌ FAIL"
        if is_correct and tools_match and result["success"]:
            passed += 1
        
        print(f"\n📊 Статус: {status}")
        print(f"   ⏱️  Время: {elapsed:.1f}с")
        print(f"   🔄 Итераций: {result['iterations']}")
        print(f"   🛠️  Инструменты: {used_tools or 'не использованы'}")
        print(f"   ✅ Проверка ответа: {'OK' if is_correct else 'FAIL'}")
        print(f"   ✅ Инструменты: {'OK' if tools_match else 'FAIL'}")
        
        if answer:
            preview = answer[:150] + "..." if len(answer) > 150 else answer
            print(f"   💬 Ответ: {preview}")
        
        results.append({
            "test_id": test["id"],
            "question": test["question"],
            "success": result["success"],
            "answer_correct": is_correct,
            "tools_match": tools_match,
            "overall": is_correct and tools_match and result["success"],
            "iterations": result["iterations"],
            "time_sec": round(elapsed, 2),
            "used_tools": used_tools,
            "answer_preview": answer[:200]
        })
    
    # Итоговая статистика
    success_rate = passed / len(test_cases) * 100
    
    print(f"\n{'='*70}")
    print(f"📈 ИТОГИ:")
    print(f"   Пройдено: {passed}/{len(test_cases)} тестов")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Требуется: ≥80%")
    print(f"   Статус: {'✅ ЗАЧЁТ' if success_rate >= 80 else '❌ НЕ ЗАЧЁТ'}")
    print(f"{'='*70}\n")
    
    return {
        "total": len(test_cases),
        "passed": passed,
        "success_rate": success_rate,
        "results": results
    }


def main():
    """Точка входа для оценки."""
    # Инициализация агента с отключённым выводом для чистого лога
    agent = ReActAgent(verbose=True)
    
    # Запуск оценки
    report = evaluate_agent(agent, TEST_CASES)
    
    # Сохранение отчёта
    with open("evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"💾 Отчёт сохранён в evaluation_report.json")
    
    return report["success_rate"] >= 80


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)