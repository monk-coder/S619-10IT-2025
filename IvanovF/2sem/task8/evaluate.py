from agent import ReActAgent

agent = ReActAgent()

tests = [
    "Какая погода в Москве завтра?",
    "Сколько будет 15% от 250000 рублей?",
    "Найди информацию про архитектуру Transformer",
    "Переведи 5000 рублей в евро (текущий курс)",
    "Что такое RAG в контексте LLM?"
]

success = 0

for i, test in enumerate(tests, 1):

    print("\n===================================")
    print(f"ТЕСТ {i}: {test}")
    print("===================================\n")

    try:
        answer = agent.run(test)

        print("\nОТВЕТ:")
        print(answer)

        if answer and "Ошибка" not in answer:
            success += 1

    except Exception as e:
        print("Ошибка теста:", e)

print("\n======================")
print(f"SUCCESS RATE: {success}/5")
print("======================")