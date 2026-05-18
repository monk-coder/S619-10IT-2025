from utils import load_model_and_tokenizer, ask_question

def main():
    print("Загрузка базовой модели Llama и твоего адаптера LoRA с Hugging Face...")
    model, tokenizer = load_model_and_tokenizer()

    test_cases = [
        {
            "context": "The Amazon rainforest is a moist broadleaf tropical rainforest in the Amazon biome.",
            "question": "What type of rainforest is the Amazon?"
        },
        {
            "context": "Super Bowl 50 was an American football game to determine the champion of the NFL for the 2015 season.",
            "question": "Which season did Super Bowl 50 determine the champion for?"
        },
        {
            "context": "There are no valid answers to this question in the database.",
            "question": "What is the meaning of life according to SQuAD?"
        }
    ]

    print("\n--- ЗАПУСК ЛОКАЛЬНОГО ИНФЕРЕНСА ---")
    for i, case in enumerate(test_cases, 1):
        answer = ask_question(model, tokenizer, case['context'], case['question'])
        print(f"\nПример {i}:")
        print(f"Вопрос: {case['question']}")
        print(f"Ответ твоей модели: {answer}")

if __name__ == "__main__":
    main()