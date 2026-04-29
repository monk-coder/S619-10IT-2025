"""
ReAct Agent: цикл Reasoning + Acting с инструментами.
"""
import re
import json
import os
from typing import Optional, List, Dict, Tuple
from dotenv import load_dotenv

import ollama
from tools import TOOLS, get_tool_schema

load_dotenv()


class ReActAgent:
    """ReAct Agent с поддержкой инструментов и защитой от бесконечных циклов."""
    
    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.tools_list = list(TOOLS.keys())
        
        # Подготовка схем инструментов для Ollama
        self.tool_schemas = [get_tool_schema(name) for name in self.tools_list]
    
    def _print(self, *args, **kwargs):
        """Вывод только если verbose=True."""
        if self.verbose:
            print(*args, **kwargs)
    
    def _parse_action(self, content: str) -> Optional[Tuple[str, List[str]]]:
        """
        Парсит Action из ответа модели.
        Возвращает (tool_name, [args]) или None.
        
        Поддерживает форматы:
        - tool_name["arg"]
        - tool_name["arg1", "arg2"]
        """
        # Паттерн: tool_name["args"]
        pattern = r'(\w+)\s*\[\s*([^\]]+)\s*\]'
        match = re.search(pattern, content)
        if not match:
            return None
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
        # Парсинг аргументов (упрощённый — разделяем по запятой)
        args = [arg.strip().strip('"').strip("'") for arg in args_str.split(",")]
        args = [a for a in args if a]  # убрать пустые
        
        return tool_name, args
    
    def _execute_tool(self, tool_name: str, args: List[str]) -> str:
        """Выполняет инструмент и возвращает результат."""
        if tool_name not in TOOLS:
            return f"Ошибка: инструмент '{tool_name}' не найден. Доступные: {', '.join(TOOLS.keys())}"
        
        tool_func = TOOLS[tool_name]
        try:
            # Вызов с распаковкой аргументов
            import inspect
            sig = inspect.signature(tool_func)
            params = list(sig.parameters.keys())
            
            if len(args) > len(params):
                args = args[:len(params)]  # обрезать лишние
            
            # Если аргументов меньше — дополняем None (для опциональных)
            while len(args) < len(params):
                param = params[len(args)]
                if sig.parameters[param].default is not inspect.Parameter.empty:
                    args.append(sig.parameters[param].default)
                else:
                    args.append("")  # пустая строка как fallback
            
            result = tool_func(*args)
            return str(result)
        except Exception as e:
            return f"Ошибка выполнения {tool_name}: {type(e).__name__}: {str(e)}"
    
    def _build_messages(self, question: str) -> List[Dict]:
        """Строит начальный список сообщений."""
        from prompts import SYSTEM_PROMPT
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}"}
        ]
    
    def run(self, question: str) -> Dict:
        """
        Запускает ReAct цикл для вопроса.
        
        Returns:
            Dict с результатом:
            - answer: финальный ответ
            - trace: список шагов (Thought/Action/Observation)
            - success: был ли достигнут финальный ответ
            - iterations: количество итераций
        """
        messages = self._build_messages(question)
        trace = []
        iteration = 0
        final_answer = None
        
        self._print(f"\n{'='*60}")
        self._print(f"🤖 Запрос: {question}")
        self._print(f"{'='*60}\n")
        
        while iteration < self.max_iterations:
            iteration += 1
            self._print(f"\n🔄 Итерация {iteration}/{self.max_iterations}")
            
            try:
                # Запрос к модели с tool calling
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
                
                # Логирование рассуждений
                if content.strip():
                    self._print(f"💭 Thought: {content.strip()}")
                    trace.append({"step": "thought", "content": content.strip()})
                
                # Проверка на финальный ответ
                if "Final Answer:" in content or "final answer:" in content.lower():
                    # Извлечение ответа
                    match = re.search(r'Final Answer:\s*(.+?)(?:\n\n|\Z)', content, re.DOTALL | re.IGNORECASE)
                    if match:
                        final_answer = match.group(1).strip()
                    else:
                        # Если нет явного маркера — берём всё после Final Answer
                        parts = re.split(r'Final Answer:\s*', content, flags=re.IGNORECASE)
                        final_answer = parts[-1].strip() if len(parts) > 1 else content.strip()
                    
                    self._print(f"✅ Final Answer: {final_answer}")
                    trace.append({"step": "final_answer", "content": final_answer})
                    break
                
                # Обработка tool calls (приоритет над парсингом из content)
                if tool_calls:
                    for call in tool_calls:
                        tool_name = call['function']['name']
                        args_dict = call['function'].get('arguments', {})
                        args = list(args_dict.values()) if args_dict else []
                        
                        self._print(f"🔧 Action: {tool_name}[{', '.join(f'\"{a}\"' for a in args)}]")
                        trace.append({"step": "action", "tool": tool_name, "args": args})
                        
                        observation = self._execute_tool(tool_name, args)
                        self._print(f"📥 Observation: {observation[:200]}{'...' if len(observation) > 200 else ''}")
                        trace.append({"step": "observation", "content": observation})
                        
                        # Добавляем в контекст
                        messages.append({
                            "role": "tool",
                            "tool_name": tool_name,
                            "content": observation
                        })
                
                # Если нет tool_calls, пробуем распарсить Action из content
                elif action := self._parse_action(content):
                    tool_name, args = action
                    self._print(f"🔧 Action: {tool_name}[{', '.join(f'\"{a}\"' for a in args)}]")
                    trace.append({"step": "action", "tool": tool_name, "args": args})
                    
                    observation = self._execute_tool(tool_name, args)
                    self._print(f"📥 Observation: {observation[:200]}{'...' if len(observation) > 200 else ''}")
                    trace.append({"step": "observation", "content": observation})
                    
                    messages.append({
                        "role": "assistant",
                        "content": content
                    })
                    messages.append({
                        "role": "tool",
                        "tool_name": tool_name,
                        "content": observation
                    })
                
                else:
                    # Нет ни tool_calls, ни Action — возможно, модель дала ответ без форматирования
                    if "Final Answer:" not in content and iteration < self.max_iterations:
                        # Подталкиваем к формату
                        messages.append({
                            "role": "assistant",
                            "content": content + "\n\nПожалуйста, используй формат Action: tool_name[\"args\"] или заверши ответ через Final Answer:"
                        })
                        continue
                    else:
                        final_answer = content.strip()
                        self._print(f"✅ Final Answer: {final_answer}")
                        trace.append({"step": "final_answer", "content": final_answer})
                        break
                
                # Добавляем ответ ассистента в историю
                if not tool_calls:
                    messages.append({"role": "assistant", "content": content})
                
            except ollama.ResponseError as e:
                error_msg = f"Ошибка API Ollama: {str(e)}"
                self._print(f"❌ {error_msg}")
                trace.append({"step": "error", "content": error_msg})
                
                # Пробуем продолжить с сообщением об ошибке
                messages.append({
                    "role": "assistant",
                    "content": f"Произошла ошибка при вызове инструмента: {str(e)}. Попробую другой подход."
                })
                continue
                
            except Exception as e:
                error_msg = f"Неожиданная ошибка: {type(e).__name__}: {str(e)}"
                self._print(f"❌ {error_msg}")
                trace.append({"step": "error", "content": error_msg})
                break
        
        # Проверка на превышение итераций
        if iteration >= self.max_iterations and not final_answer:
            self._print(f"\n⚠️ Достигнут лимит итераций ({self.max_iterations})")
            final_answer = "Не удалось завершить задачу в пределах лимита итераций. Попробуйте упростить запрос."
            trace.append({"step": "final_answer", "content": final_answer, "warning": "max_iterations reached"})
        
        return {
            "answer": final_answer,
            "trace": trace,
            "success": final_answer is not None and "max_iterations" not in str(trace[-1].get("warning", "")),
            "iterations": iteration
        }


def main():
    """Тестовый запуск агента."""
    import sys
    
    # Инициализация
    agent = ReActAgent(verbose=True)
    
    # Если передан вопрос в аргументах — выполнить его
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        result = agent.run(question)
        print(f"\n📊 Результат: {'✅ Успех' if result['success'] else '❌ Неудача'}")
        print(f"   Итераций: {result['iterations']}")
        return result['answer']
    
    # Интерактивный режим
    print("🤖 ReAct Agent запущен. Введите вопрос или 'exit' для выхода.")
    while True:
        try:
            question = input("\n❓ Вопрос: ").strip()
            if question.lower() in ('exit', 'quit', 'выход'):
                break
            if not question:
                continue
            
            result = agent.run(question)
            print(f"\n📊 Результат: {'✅ Успех' if result['success'] else '❌ Неудача'}")
            print(f"   Итераций: {result['iterations']}")
            if result['answer']:
                print(f"\n💬 Ответ: {result['answer']}")
                
        except KeyboardInterrupt:
            print("\n👋 Завершение работы.")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    main()