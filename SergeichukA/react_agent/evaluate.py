"""
Модуль автоматической оценки агента.
"""

import time
import json
import logging
from typing import Callable, Any
from agent import ReActAgent

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# Проверочные функции
def check_weather(answer: str) -> bool:
    if not answer:
        return False
    a = answer.lower()
    return any(x in a for x in ["°c", "градус", "погода", "температур", "облач", "ветер"])


def check_calculator(answer: str, expected: str) -> bool:
    return expected in answer if answer else False


def check_search_length(answer: str, min_length: int = 50) -> bool:
    return len(answer or "") >= min_length


def check_contains_keywords(answer: str, **kwargs) -> bool:
    """
    Проверка: ответ содержит хотя бы одно из ключевых слов.
    Вызов: check_contains_keywords(answer, keywords=["word1", "word2"])
    """
    if not answer:
        return False
    keywords = kwargs.get("keywords", [])
    if not keywords:
        return True
    answer_lower = answer.lower()
    return any(str(kw).lower() in answer_lower for kw in keywords)


# Тест-кейсы
TEST_CASES: list[dict[str, Any]] = [
    {
        "id": 1,
        "question": "Какая погода в Москве завтра?",
        "expected_tools": ["get_weather"],
        "check": check_weather,
        "check_args": {}
    },
    {
        "id": 2,
        "question": "Сколько будет 15% от 250000 рублей?",
        "expected_tools": ["calculator"],
        "check": check_calculator,
        "check_args": {"expected": "37500"}
    },
    {
        "id": 3,
        "question": "Найди информацию про архитектуру Transformer",
        "expected_tools": ["web_search"],
        "check": check_contains_keywords,
        "check_args": {"keywords": ["attention", "transformer", "нейросеть", "модель", "bert", "gpt", "deep learning"]}
    },
    {
        "id": 4,
        "question": "Переведи 5000 рублей в евро",
        "expected_tools": ["web_search", "calculator"],
        "check": check_contains_keywords,
        "check_args": {"keywords": ["€", "евро", "курс", "5000", "66", "67", "60", "70", "примерно", "около", "руб"]}
    },
    {
        "id": 5,
        "question": "Что такое RAG в контексте больших языковых моделей?",
        "expected_tools": ["web_search"],
        "check": check_contains_keywords,
        "check_args": {"keywords": ["rag", "retrieval", "поиск", "документ", "контекст", "llm", "generation"]}
    }
]


def evaluate_agent(agent: ReActAgent, test_cases: list[dict]) -> dict[str, Any]:
    results: list[dict] = []
    passed = 0
    
    logger.info(f"\n{'='*70}\n🧪 Оценка: {len(test_cases)} тестов\n{'='*70}\n")
    
    for test in test_cases:
        logger.info(f"📋 Тест #{test['id']}: {test['question'][:50]}...")
        
        start = time.time()
        result = agent.run(test["question"])
        elapsed = time.time() - start
        
        answer = result.get("answer", "") or ""
        
        try:
            is_correct = test["check"](answer, **test.get("check_args", {}))
        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки: {e}")
            is_correct = False
        
        used_tools = [s.get("tool") for s in result.get("trace", []) if s.get("step") == "action" and s.get("tool")]
        expected = test.get("expected_tools", [])
        tools_match = any(et in used_tools for et in expected) if expected else True
        
        overall = is_correct and tools_match and result.get("success", False)
        if overall:
            passed += 1
        
        status = "✅ PASS" if overall else "❌ FAIL"
        logger.info(f"  {status} | ⏱️{elapsed:.1f}с | 🔄{result.get('iterations',0)} | 🛠️{used_tools or '-'}")
        if answer and len(answer) < 200:
            logger.info(f"  💬 {answer}")
        
        results.append({
            "test_id": test["id"], "question": test["question"],
            "success": result.get("success"), "answer_correct": is_correct,
            "tools_match": tools_match, "overall": overall,
            "iterations": result.get("iterations"), "time_sec": round(elapsed, 2),
            "used_tools": used_tools, "answer_preview": answer[:200] if answer else ""
        })
    
    rate = (passed / len(test_cases)) * 100 if test_cases else 0
    logger.info(f"\n{'='*70}\n📈 ИТОГИ: {passed}/{len(test_cases)} | {rate:.1f}% | {'✅ ЗАЧЁТ' if rate >= 80 else '❌'}\n{'='*70}\n")
    
    return {
        "total": len(test_cases), "passed": passed, "success_rate": round(rate, 2),
        "passed_threshold": rate >= 80, "results": results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def main() -> bool:
    agent = ReActAgent(verbose=True)
    report = evaluate_agent(agent, TEST_CASES)
    with open("evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report["passed_threshold"]


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)