import re
import os
from dotenv import load_dotenv
import ollama
from tools import TOOLS, get_tool_schema

load_dotenv()

class ReActAgent:
    def __init__(self, model=None, base_url=None, max_iterations=10, verbose=True):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.tools_list = list(TOOLS.keys())
        self.tool_schemas = [get_tool_schema(name) for name in self.tools_list]

    def _print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def _run_tool(self, tool_name, args, messages):
        """Единый метод для выполнения инструмента (убирает дублирование кода)"""
        self._print(f"🔧 Action: {tool_name}[{', '.join(f'\"{a}\"' for a in args)}]")
        
        observation = ""
        if tool_name in TOOLS:
            try:
                # Выполняем инструмент
                func = TOOLS[tool_name]
                observation = str(func(*args))
            except Exception as e:
                observation = f"Ошибка выполнения {tool_name}: {str(e)}"
        else:
            observation = f"Ошибка: инструмент '{tool_name}' не найден."

        self._print(f"📥 Observation: {observation[:150]}{'...' if len(observation) > 150 else ''}")
        
        # Добавляем результат в историю
        messages.append({"role": "tool", "tool_name": tool_name, "content": observation})
        return observation

    def run(self, question):
        from prompts import SYSTEM_PROMPT
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}"}
        ]
        trace = []
        iteration = 0
        final_answer = None

        self._print(f"\n{'='*60}\n🤖 Запрос: {question}\n{'='*60}\n")

        while iteration < self.max_iterations:
            iteration += 1
            self._print(f"\n🔄 Итерация {iteration}/{self.max_iterations}")

            try:
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    tools=self.tool_schemas,
                    options={"temperature": 0.1, "num_predict": 1024},
                    stream=False
                )
                
                message = response['message']
                content = message.get('content', '')
                tool_calls = message.get('tool_calls', [])

                # Логика выбора действия
                action_handled = False

                # Вариант 1: Нативный вызов через Ollama (JSON)
                if tool_calls:
                    for call in tool_calls:
                        self._run_tool(call['function']['name'], list(call['function']['arguments'].values()), messages)
                        action_handled = True
                
                # Вариант 2: Парсинг из текста (Regex fallback)
                elif content:
                    match = re.search(r'(\w+)\s*\[\s*([^\]]+)\s*\]', content)
                    if match:
                        tool_name = match.group(1)
                        args = [a.strip().strip('"') for a in match.group(2).split(",")]
                        self._run_tool(tool_name, args, messages)
                        messages.append({"role": "assistant", "content": content})
                        action_handled = True

                # Проверка на финальный ответ
                if "Final Answer:" in content:
                    match = re.search(r'Final Answer:\s*(.+)', content, re.IGNORECASE)
                    final_answer = match.group(1).strip() if match else content.strip()
                    self._print(f"✅ Final Answer: {final_answer}")
                    trace.append({"step": "final_answer", "content": final_answer})
                    break
                
                # Если модель просто болтает без действий
                elif not action_handled:
                     messages.append({"role": "assistant", "content": content})

            except Exception as e:
                self._print(f"❌ Ошибка: {str(e)}")
                break

        if not final_answer:
            final_answer = "Не удалось завершить задачу."
            self._print(f"\n⚠️ Лимит итераций. Ответ: {final_answer}")

        return {"answer": final_answer, "trace": trace, "success": bool(final_answer), "iterations": iteration}

def main():
    import sys
    agent = ReActAgent(verbose=True)
    if len(sys.argv) > 1:
        result = agent.run(" ".join(sys.argv[1:]))
        print(f"\n📊 Результат: {'✅' if result['success'] else '❌'}")
    else:
        print("🤖 ReAct Agent запущен. Введите вопрос или 'exit'.")
        while True:
            try:
                q = input("\n❓ Вопрос: ").strip()
                if q.lower() in ('exit', 'quit'): break
                if q: agent.run(q)
            except KeyboardInterrupt: break

if __name__ == "__main__":
    main()
