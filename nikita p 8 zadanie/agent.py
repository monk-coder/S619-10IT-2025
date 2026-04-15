"""
ReAct Agent: цикл рассуждений + действий.
Запускается локально через Ollama + llama3.2:1b.
"""
import re
import json
import time
from typing import Optional, List, Tuple
from dotenv import load_dotenv
import ollama

from tools import TOOLS, get_tool_schema
from prompts import REACT_SYSTEM_PROMPT, format_action

load_dotenv()

class ReActAgent:
    def __init__(
        self,
        model: str = "llama3.2:1b",
        host: str = "http://localhost:11434",
        max_iterations: int = 10,
        verbose: bool = True
    ):
        self.model = model
        self.host = host
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.client = ollama.Client(host=host)
        self.history: List[dict] = []
        
    def _log(self, message: str):
        if self.verbose:
            print(message)
    
    def _parse_action(self, text: str) -> Optional[Tuple[str, List[str]]]:
        """
        Парсит Action из ответа LLM.
        Ожидает формат: tool_name["arg1", "arg2"] или tool_name["arg"]
        """
        # Ищем паттерн: name["..."] или name["...", "..."]
        pattern = r'(\w+)\[([^\]]+)\]'
        match = re.search(pattern, text)
        if not match:
            return None
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
        # Парсим аргументы в кавычках
        args = re.findall(r'"([^"]*)"', args_str)
        
        if tool_name not in TOOLS:
            self._log(f"⚠️ Инструмент '{tool_name}' не найден")
            return None
        
        return tool_name, args
    
    def _execute_tool(self, tool_name: str, args: List[str]) -> str:
        """Выполняет инструмент и возвращает observation."""
        tool = TOOLS[tool_name]
        try:
            # Вызываем с распаковкой аргументов
            result = tool(*args)
            return str(result)
        except TypeError as e:
            # Возможно, аргументов меньше/больше — пробуем передать как один строковый аргумент
            if len(args) == 1:
                try:
                    return str(tool(args[0]))
                except:
                    pass
            return f"Ошибка вызова {tool_name}: {str(e)}"
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def _build_messages(self, query: str, trace: List[str]) -> List[dict]:
        """Формирует список сообщений для LLM."""
        messages = [
            {"role": "system", "content": REACT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Задача: {query}"}
        ]
        
        # Добавляем историю трейса
        if trace:
            messages.append({"role": "assistant", "content": "\n".join(trace)})
        
        return messages
    
    def _check_final_answer(self, text: str) -> Optional[str]:
        """Проверяет, есть ли в ответе Final Answer."""
        pattern = r'Final Answer:\s*(.+?)(?:\n\n|\n$|$)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def run(self, query: str) -> dict:
        """
        Запускает цикл ReAct.
        
        Returns:
            dict с результатом: ответ, трейс, статус, итерации
        """
        trace: List[str] = []
        iteration = 0
        error_count = 0
        
        self._log(f"\n🚀 Запуск агента: '{query}'")
        self._log("=" * 60)
        
        while iteration < self.max_iterations:
            iteration += 1
            self._log(f"\n[Итерация {iteration}/{self.max_iterations}]")
            
            # Формируем запрос к LLM
            messages = self._build_messages(query, trace)
            
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": 0.1, "num_predict": 512}
                )
                assistant_reply = response['message']['content'].strip()
                
            except Exception as e:
                error_msg = f"Ошибка LLM: {str(e)}"
                self._log(f"❌ {error_msg}")
                return {
                    "answer": f"Не удалось получить ответ: {error_msg}",
                    "trace": trace,
                    "status": "llm_error",
                    "iterations": iteration
                }
            
            self._log(f"🤖 LLM: {assistant_reply[:200]}{'...' if len(assistant_reply) > 200 else ''}")
            
            # Проверяем Final Answer
            final_answer = self._check_final_answer(assistant_reply)
            if final_answer:
                self._log(f"\n✅ Final Answer: {final_answer}")
                trace.append(f"Final Answer: {final_answer}")
                return {
                    "answer": final_answer,
                    "trace": trace,
                    "status": "success",
                    "iterations": iteration
                }
            
            # Парсим Action
            action = self._parse_action(assistant_reply)
            if not action:
                self._log("⚠️ Не удалось распарсить Action")
                trace.append(f"Thought: {assistant_reply}")
                # Подсказываем формат
                trace.append("Observation: Ошибка формата. Используйте: Action: tool_name[\"arg\"]")
                error_count += 1
                if error_count >= 3:
                    return {
                        "answer": "Не удалось выполнить задачу: агент не может сформировать корректный Action.",
                        "trace": trace,
                        "status": "parse_error",
                        "iterations": iteration
                    }
                continue
            
            tool_name, args = action
            self._log(f"🔧 Action: {tool_name}[{', '.join(f'\"{a}\"' for a in args)}]")
            
            # Выполняем инструмент
            observation = self._execute_tool(tool_name, args)
            self._log(f"📥 Observation: {observation[:150]}{'...' if len(observation) > 150 else ''}")
            
            # Добавляем в трейс
            trace.append(f"Thought: <рассуждение>")
            trace.append(f"Action: {format_action(tool_name, args)}")
            trace.append(f"Observation: {observation}")
            
            # Если инструмент вернул ошибку — увеличиваем счётчик
            if observation.startswith("Ошибка"):
                error_count += 1
                self._log(f"⚠️ Ошибка инструмента ({error_count}/3)")
                if error_count >= 3:
                    trace.append("Observation: Слишком много ошибок. Попробуйте другой подход.")
        
        # Превышено количество итераций
        self._log(f"\n⚠️ Достигнут лимит итераций ({self.max_iterations})")
        return {
            "answer": "Не удалось завершить задачу за отведённое число шагов. Попробуйте упростить запрос.",
            "trace": trace,
            "status": "max_iterations",
            "iterations": iteration
        }


def quick_test():
    """Быстрый тест агента."""
    agent = ReActAgent(verbose=True)
    
    # Тест калькулятора
    result = agent.run("Сколько будет 25 * 4 + 10?")
    print(f"\n📊 Результат: {result['answer']}")
    print(f"📈 Статус: {result['status']}, итераций: {result['iterations']}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Какая погода в Москве?"
    
    agent = ReActAgent(verbose=True)
    result = agent.run(query)
    
    print("\n" + "="*60)
    print(f"✅ ОТВЕТ: {result['answer']}")
    print(f"📊 Статус: {result['status']}")
    print(f"🔄 Итераций: {result['iterations']}")
    print("="*60)
