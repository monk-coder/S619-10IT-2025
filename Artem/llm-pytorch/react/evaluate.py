import sys
from tools import web_search, calculator, get_weather, currency_converter
from agent import ReActAgent

def run_test_case(agent, question, expected_keywords):
    print(f"\n{'='*60}\nТест: {question}\n{'='*60}")
    try:
        answer, trace = agent.run(question, verbose=True)
        print(f"\nОтвет: {answer}")
        answer_lower = answer.lower()
        if all(kw.lower() in answer_lower for kw in expected_keywords):
            print("✅ PASS")
            return True, answer
        else:
            print(f"❌ FAIL (ожидались ключевые слова: {expected_keywords})")
            return False, answer
    except Exception as e:
        print(f"❌ FAIL с исключением: {e}")
        return False, str(e)

def main():
    tools = {
        "web_search": web_search,
        "calculator": calculator,
        "get_weather": get_weather,
        "currency_converter": currency_converter,
    }
    agent = ReActAgent(tools, model="llama3.2:1b", max_iterations=10)

    test_cases = [
        ("Какая погода в Москве завтра?", ["температур", "°C", "град"]),
        ("Сколько будет 15% от 250000 рублей?", ["37500"]),
        ("Найди информацию про архитектуру Transformer", ["transformer", "внимания", "attention"]),
        ("Переведи 5000 рублей в евро (текущий курс)", ["евро", "eur"]),
        ("Что такое RAG в контексте LLM?", ["retrieval", "augmented", "generation", "rag"]),
    ]

    results = []
    for question, keywords in test_cases:
        passed, _ = run_test_case(agent, question, keywords)
        results.append(passed)

    success_rate = sum(results) / len(results) * 100
    print(f"\n{'='*60}")
    print(f"Success rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    if success_rate >= 80:
        print("✅ Минимальный критерий выполнен (>=80%)")
    else:
        print("❌ Минимальный критерий не выполнен")

    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())