"""
Модуль ReAct Agent — агент с циклом рассуждение-действие-наблюдение.
Версия с улучшенной детекцией ответов и обработкой ошибок.
"""

import re
import os
import json
import logging
import time
from typing import Any, Optional, Union
from dotenv import load_dotenv
import ollama

from tools import TOOLS, get_tool_schema

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()


class ReActAgent:
    """
    ReAct Agent для решения задач через чередование рассуждений и действий.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_iterations: int = 10,
        verbose: bool = True,
        temperature: float = 0.2
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.temperature = temperature
        
        self.tools_list = list(TOOLS.keys())
        self.tool_schemas = [get_tool_schema(name) for name in self.tools_list]
        
        try:
            self.client = ollama.Client(host=self.base_url) if self.base_url else ollama.Client()
        except Exception as e:
            logger.warning(f"⚠️ Не удалось подключиться к Ollama: {e}")
            self.client = None
    
    def _log(self, message: str, level: str = "info") -> None:
        """Внутренний метод логирования."""
        if self.verbose:
            getattr(logger, level)(message)
    
    def _normalize_tool_args(self, tool_name: str, args: list[str]) -> list[str]:
        """Нормализует аргументы инструмента с учётом ожидаемого порядка."""
        if tool_name == "web_search":
            if len(args) == 2:
                if args[0].isdigit() and not args[1].isdigit():
                    self._log(f"🔀 web_search: меняем аргументы: [{args[1]}, {args[0]}]")
                    return [args[1], args[0]]
            if len(args) == 1:
                return [args[0], "3"]
            return args
        
        elif tool_name == "calculator":
            if len(args) > 1:
                combined = " ".join(args)
                self._log(f"🔀 calculator: объединяем аргументы: '{combined}'")
                return [combined]
            return args
        
        elif tool_name == "get_weather":
            if len(args) == 2:
                if args[0].isdigit() and not args[1].isdigit():
                    return [args[1], args[0]]
            if len(args) == 1:
                return [args[0], "3"]
            return args
        
        return args
    
    def _run_tool(self, tool_name: str, args: list[str], messages: list[dict]) -> str:
        """Выполняет инструмент с нормализацией аргументов."""
        normalized_args = self._normalize_tool_args(tool_name, args)
        self._log(f"🔧 Action: {tool_name}[{', '.join(f'\"{a}\"' for a in normalized_args)}]")
        
        observation: str
        if tool_name not in TOOLS:
            available = ", ".join(TOOLS.keys())
            observation = f"Ошибка: инструмент '{tool_name}' не найден. Доступные: {available}"
        else:
            try:
                func = TOOLS[tool_name]
                result = func(*normalized_args)
                observation = str(result)
            except TypeError as e:
                try:
                    sig_params = list(func.__code__.co_varnames[:func.__code__.co_argcount])
                    trimmed_args = normalized_args[:len(sig_params)]
                    result = func(*trimmed_args)
                    observation = str(result)
                    self._log(f"🔁 Повторный вызов с аргументами: {trimmed_args}")
                except Exception as e2:
                    observation = f"Ошибка {tool_name}: {type(e).__name__}"
            except Exception as e:
                observation = f"Ошибка {tool_name}: {type(e).__name__}"
        
        preview = observation[:200] + ("..." if len(observation) > 200 else "")
        self._log(f"📥 Observation: {preview}")
        
        messages.append({
            "role": "tool",
            "tool_name": tool_name,
            "content": observation
        })
        
        return observation
    
    def _parse_action_from_text(self, content: str) -> Optional[tuple[str, list[str]]]:
        """Парсит действие из текста модели."""
        patterns = [
            r'(\w+)\s*\[\s*"([^"]+)"\s*(?:,\s*"([^"]+)")*\s*\]',
            r"(\w+)\s*\[\s*'([^']+)'\s*(?:,\s*'([^']+)')*\s*\]",
            r'(\w+)\s*\[\s*([^\]]+)\s*\]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                tool_name = match.group(1)
                args_str = match.group(0)[match.group(0).find('[')+1 : match.group(0).rfind(']')]
                args = re.findall(r'["\']?([^"\',\]]+)["\']?', args_str)
                args = [a.strip() for a in args if a.strip()]
                if tool_name and args:
                    return tool_name, args
        
        return None
    
    def _check_final_answer(self, content: str) -> Optional[str]:
        """Расширенная детекция финального ответа."""
        if not content:
            return None
        
        content_stripped = content.strip()
        content_lower = content_stripped.lower()
        
        # 1. Явные маркеры
        final_patterns = [
            r'Final Answer:\s*(.+?)(?:\n\n|\n$|$)',
            r'(?:Ответ|Итог|Результат|Вывод|Итак|Заключение):\s*(.+?)(?:\n\n|\n$|$)',
            r'###\s*(?:Ответ|Answer|Result|Conclusion):\s*(.+?)(?:\n\n|\n$|$)',
        ]
        
        for pattern in final_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                if answer and len(answer) > 3:
                    return answer
        
        # 2. Если контент не содержит служебных слов действий
        action_keywords = ['action:', 'tool_', 'calculator[', 'web_search[', 'get_weather[']
        if not any(kw in content_lower for kw in action_keywords):
            cleaned = re.sub(r'^(Thought|Thinking|Итак|Так|Хорошо|Окей|Based on|According)[:\s]*', '', 
                           content_stripped, flags=re.IGNORECASE).strip()
            
            if cleaned and len(cleaned) >= 10:
                answer_indicators = [
                    'трансформер', 'transformer', 'архитектур', 'нейросет', 'rag', 'retrieval',
                    'поиск', 'документ', 'евро', 'курс', 'рубл', 'градус', 'погод', 'температур',
                    'равно', 'составляет', 'это', 'является'
                ]
                if any(ind in cleaned.lower() for ind in answer_indicators):
                    return cleaned
        
        # 3. Последняя непустая строка
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        if lines:
            last = lines[-1]
            if (len(last) >= 15 and 
                not any(kw in last.lower() for kw in ['action:', 'thought:', 'observation:', 'tool_']) and
                any(c.isalpha() for c in last)):
                return last
        
        return None
    
    def _build_result(
        self,
        answer: str,
        trace: list[dict],
        iterations: int,
        success: bool
    ) -> dict[str, Any]:
        """Формирует структурированный результат."""
        return {
            "answer": answer,
            "trace": trace,
            "success": success,
            "iterations": iterations,
            "model": self.model,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _should_retry_tool_call(self, observation: str) -> bool:
        """Определяет, стоит ли повторить вызов инструмента."""
        retry_keywords = [
            "недопустимые символы", "ошибка синтаксиса", 
            "неверный аргумент", "TypeError", "missing"
        ]
        obs_lower = observation.lower()
        return any(kw in obs_lower for kw in retry_keywords)
    
    def run(self, question: str) -> dict[str, Any]:
        """Основной метод выполнения задачи."""
        from prompts import build_system_prompt
        
        if not self.client:
            return self._build_result(
                answer="Ошибка: не удалось подключиться к Ollama",
                trace=[], iterations=0, success=False
            )
        
        system_prompt = build_system_prompt(TOOLS)
        
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}"}
        ]
        
        trace: list[dict] = []
        final_answer: Optional[str] = None
        last_observation: Optional[str] = None
        
        self._log(f"\n{'='*60}\n🤖 Запрос: {question}\n{'='*60}\n")
        
        for iteration in range(1, self.max_iterations + 1):
            self._log(f"\n🔄 Итерация {iteration}/{self.max_iterations}")
            
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    tools=self.tool_schemas,
                    options={
                        "temperature": self.temperature,
                        "num_predict": 1500,
                        "stop": ["Final Answer:", "###"]
                    }
                )
                
                message = response.get('message', {})
                content = message.get('content', '') or ''
                tool_calls = message.get('tool_calls', [])
                
                action_handled = False
                retry_needed = False
                
                # === Вариант 1: Нативные tool_calls ===
                if tool_calls:
                    for call in tool_calls:
                        func_info = call.get('function', {})
                        tool_name = func_info.get('name')
                        arguments = func_info.get('arguments', {})
                        
                        if tool_name:
                            args = list(arguments.values())
                            observation = self._run_tool(tool_name, args, messages)
                            
                            trace.append({
                                "step": "action",
                                "iteration": iteration,
                                "tool": tool_name,
                                "arguments": arguments,
                                "observation": observation[:500]
                            })
                            
                            last_observation = observation
                            
                            if self._should_retry_tool_call(observation) and iteration < self.max_iterations:
                                retry_needed = True
                                self._log("🔁 Ошибка аргументов, пробуем альтернативный формат...")
                            
                            action_handled = True
                
                # === Вариант 2: Парсинг из текста ===
                elif content.strip():
                    parsed = self._parse_action_from_text(content)
                    if parsed:
                        tool_name, args = parsed
                        observation = self._run_tool(tool_name, args, messages)
                        
                        trace.append({
                            "step": "action",
                            "iteration": iteration,
                            "tool": tool_name,
                            "arguments": args,
                            "observation": observation[:500]
                        })
                        
                        last_observation = observation
                        
                        if self._should_retry_tool_call(observation) and iteration < self.max_iterations:
                            retry_needed = True
                        
                        action_handled = True
                    
                    if content.strip():
                        messages.append({"role": "assistant", "content": content})
                
                # === Проверка финального ответа ===
                final_answer = self._check_final_answer(content)
                if final_answer:
                    self._log(f"✅ Final Answer: {final_answer}")
                    trace.append({
                        "step": "final_answer",
                        "iteration": iteration,
                        "content": final_answer
                    })
                    break
                
                # === Fallback: числовое наблюдение как ответ ===
                if not final_answer and last_observation:
                    if re.match(r'^-?\d+(?:\.\d+)?\s*$', last_observation.strip()):
                        final_answer = last_observation.strip()
                        self._log(f"🔁 Fallback: числовой результат как ответ: {final_answer}")
                        trace.append({
                            "step": "final_answer_fallback",
                            "iteration": iteration,
                            "content": final_answer
                        })
                        break
                
                # === Fallback: результаты поиска как основа ответа ===
                if not final_answer and trace:
                    for step in reversed(trace):
                        if step.get("step") == "action" and step.get("tool") == "web_search":
                            obs = step.get("observation", "")
                            if obs and "Ошибка" not in obs and len(obs) > 50 and "• " in obs:
                                first_result = obs.split("• ")[1].split(":")[0] if "• " in obs else obs[:100]
                                final_answer = f"По запросу найдено: {first_result}... (для полного ответа уточните вопрос)"
                                self._log(f"🔁 Fallback: использую результат поиска как основу ответа")
                                break
                
                # === Защита от зацикливания ===
                if not action_handled and not final_answer and not retry_needed:
                    self._log("⚠️ Нет действия и нет ответа — завершаем цикл")
                    break
                    
            except ollama.ResponseError as e:
                self._log(f"❌ API Error: {e}", level="error")
                trace.append({"step": "error", "error": f"API: {str(e)}"})
                break
            except ConnectionError as e:
                self._log(f"❌ Connection Error: {e}", level="error")
                return self._build_result(
                    answer="Ошибка подключения к Ollama. Убедитесь, что сервер запущен.",
                    trace=trace, iterations=iteration, success=False
                )
            except Exception as e:
                self._log(f"❌ Unexpected Error: {type(e).__name__} — {e}", level="error")
                trace.append({"step": "error", "error": f"{type(e).__name__}: {str(e)}"})
                break
        
        # === Финализация ===
        if not final_answer:
            if last_observation and len(last_observation) < 200 and "Ошибка" not in last_observation:
                final_answer = f"Результат: {last_observation}"
            else:
                final_answer = "Не удалось сформировать ответ. Попробуйте перефразировать вопрос."
            self._log(f"\n⚠️ Используем ответ по умолчанию")
        
        success = bool(
            final_answer and 
            "не удалось" not in final_answer.lower() and 
            "ошибка" not in final_answer.lower()[:50]
        )
        
        return self._build_result(
            answer=final_answer,
            trace=trace,
            iterations=iteration,
            success=success
        )
    
    def chat(self, question: str) -> str:
        """Удобный метод для получения только текстового ответа."""
        result = self.run(question)
        return result["answer"]