import re
from ollama import chat

from tools import web_search, calculator, get_weather
from prompts import SYSTEM_PROMPT, FEW_SHOT


TOOLS = {
    "web_search": web_search,
    "calculator": calculator,
    "get_weather": get_weather
}


class ReActAgent:

    def __init__(self, model="llama3.2:1b", max_iterations=10):
        self.model = model
        self.max_iterations = max_iterations

    def run(self, question):

        history = f"""
{SYSTEM_PROMPT}

{FEW_SHOT}

Question: {question}
"""

        for step in range(self.max_iterations):

            response = chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": history
                    }
                ]
            )

            text = response["message"]["content"]

            print("\n====================")
            print(text)
            print("====================\n")

            if "Final Answer:" in text:
                final_answer = text.split("Final Answer:")[-1].strip()
                return final_answer

            action_match = re.search(r'Action:\s*(\w+)\["(.+)"\]', text)

            if not action_match:
                history += f"\nObservation: Ошибка формата Action\n"
                continue

            tool_name = action_match.group(1)
            tool_input = action_match.group(2)

            if tool_name not in TOOLS:
                history += f"\nObservation: Неизвестный tool\n"
                continue

            try:
                result = TOOLS[tool_name](tool_input)

            except Exception as e:
                result = f"Ошибка tool: {e}"

            history += f"""
{text}

Observation: {result}
"""

        return "Ошибка: превышен лимит итераций"


if __name__ == "__main__":

    agent = ReActAgent()

    question = input("Введите вопрос: ")

    answer = agent.run(question)

    print("\nFINAL ANSWER:")
    print(answer)