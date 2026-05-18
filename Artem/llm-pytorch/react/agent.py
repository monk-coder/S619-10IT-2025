import re
import json
import ast
from typing import Dict, Callable, Tuple, List
import ollama
from prompts import get_system_prompt

class ReActAgent:
    def __init__(self, tools: Dict[str, Callable], model: str = "llama3.2:1b", max_iterations: int = 10):
        self.tools = tools
        self.model = model
        self.max_iterations = max_iterations

    def _call_ollama(self, prompt: str) -> str:
        response = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
        return response['message']['content']

    def _parse_action(self, text: str) -> Tuple[str, str] | None:
        # Форматы: Action: tool["args"], Action: tool(args), Action: tool: args
        match = re.search(r"Action:\s*(\w+)\s*[\[\(](.*?)[\]\)]", text, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
        match2 = re.search(r"Action:\s*(\w+)\s*:\s*(.+)", text, re.IGNORECASE)
        if match2:
            return match2.group(1), match2.group(2)
        return None

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        if tool_name not in self.tools:
            return f"Ошибка: неизвестный инструмент '{tool_name}'"
        tool_func = self.tools[tool_name]
        try:
            # Пробуем распарсить аргументы
            if args_str.startswith('[') and args_str.endswith(']'):
                args_list = json.loads(args_str)
            else:
                args_list = ast.literal_eval(f"({args_str})")
            if not isinstance(args_list, (list, tuple)):
                args_list = [args_list]
            result = tool_func(*args_list)
            return str(result)
        except Exception as e:
            return f"Ошибка выполнения {tool_name}: {str(e)}"

    def run(self, question: str, verbose: bool = True) -> Tuple[str, List[Dict]]:
        trace = []
        current_prompt = get_system_prompt() + f"\n\nВопрос: {question}\n\nДавай подумаем шаг за шагом.\n"

        for iteration in range(self.max_iterations):
            if verbose:
                print(f"\n=== Итерация {iteration+1} ===")
            response = self._call_ollama(current_prompt)
            if verbose:
                print(f"Ответ LLM:\n{response}\n")

            trace.append({"iteration": iteration, "response": response})

            # Проверяем Final Answer
            final_match = re.search(r"Final Answer:\s*(.*)", response, re.IGNORECASE | re.DOTALL)
            if final_match:
                final_answer = final_match.group(1).strip()
                if verbose:
                    print(f"Final Answer: {final_answer}")
                return final_answer, trace

            # Ищем Action
            action = self._parse_action(response)
            if action is None:
                if verbose:
                    print("Action не найден, напоминаем формат")
                current_prompt += response + "\n\nПожалуйста, используй формат Thought/Action/Observation или Final Answer."
                continue

            tool_name, args_str = action
            if verbose:
                print(f"Action: {tool_name} с аргументами: {args_str}")

            observation = self._execute_tool(tool_name, args_str)
            if verbose:
                print(f"Observation: {observation}\n")

            current_prompt += response + f"\nObservation: {observation}\n"

        fallback_answer = "Достигнуто максимальное количество шагов. Невозможно получить ответ."
        if verbose:
            print(f"Max iterations reached. Fallback answer.")
        return fallback_answer, trace