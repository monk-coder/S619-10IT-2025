"""
Модуль инструментов для ReAct Agent.
"""

import re
import ast
import operator
import requests
import os
import inspect
from typing import Callable
from collections import defaultdict

# Используем новый пакет ddgs вместо duckduckgo_search
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


def tool(func: Callable) -> Callable:
    """Декоратор для регистрации функции как инструмента."""
    func.is_tool = True
    return func


@tool
def web_search(query: str, max_results: int = 3) -> str:
    """
    Поиск информации в интернете через DuckDuckGo.
    
    Args:
        query: Поисковый запрос (ОБЯЗАТЕЛЬНО первый аргумент)
        max_results: Максимальное количество результатов (1-10, по умолчанию 3)
    
    Returns:
        Строка с отформатированными результатами поиска
    """
    try:
        # Валидация и нормализация
        if not isinstance(query, str) or not query.strip():
            return "Ошибка: query должен быть непустой строкой"
        
        if isinstance(max_results, str):
            try:
                max_results = int(max_results)
            except ValueError:
                max_results = 3
        
        max_results = max(1, min(10, max_results))
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query.strip(), max_results=max_results):
                title = r.get('title', '')
                body = r.get('body', '')
                
                # Фильтруем нерелевантные результаты
                if title and body:
                    if any(bad in title.lower() for bad in ['ragini mms', 'ragtime music', 'ad:', 'реклама']):
                        continue
                    clean_body = ' '.join(body.split())[:200]
                    results.append(f"• {title}: {clean_body}")
        
        if not results:
            return f"Ничего релевантного не найдено по запросу '{query}'. Попробуйте уточнить запрос."
        
        return "\n".join(results)
        
    except Exception as e:
        error_msg = str(e)
        if "'>='" in error_msg or "not supported between" in error_msg:
            return f"Ошибка поиска: внутренняя ошибка API. Попробуйте упростить запрос."
        return f"Ошибка поиска: {type(e).__name__}"


@tool
def calculator(expression: str) -> str:
    """
    Безопасное вычисление математических выражений.
    Поддерживает: +, -, *, /, **, %, ^, унарный минус, скобки.
    """
    operators = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg, ast.UAdd: operator.pos,
    }
    
    def _eval(node: ast.AST) -> float | int:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Неподдерживаемый оператор: {op_type}")
            return operators[op_type](left, right)
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Неподдерживаемая унарная операция: {op_type}")
            return operators[op_type](operand)
        raise ValueError(f"Неподдерживаемый элемент AST: {type(node)}")
    
    try:
        cleaned = expression.strip()
        
        # Преобразуем ^ в ** (но только если это не часть **)
        cleaned = re.sub(r'(?<!\*)\^(?!\*)', '**', cleaned)
        cleaned = re.sub(r'\*+\*', '**', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        if not re.match(r'^[\d\s\+\-\*/%.()^*]+$', cleaned):
            return "Ошибка: выражение содержит недопустимые символы"
        
        if not cleaned:
            return "Ошибка: пустое выражение"
        
        tree = ast.parse(cleaned, mode='eval')
        result = _eval(tree.body)
        
        if isinstance(result, float):
            if result.is_integer():
                return str(int(result))
            return f"{result:.2f}"
        return str(result)
        
    except ZeroDivisionError:
        return "Ошибка: деление на ноль"
    except SyntaxError as e:
        return f"Ошибка синтаксиса: проверьте выражение (пример: '2**10' или '2^10')"
    except ValueError as e:
        return f"Ошибка вычисления: {str(e)}"
    except Exception as e:
        return f"Непредвиденная ошибка: {type(e).__name__}"


@tool
def get_weather(city: str, days: int = 3) -> str:
    """
    Получение погоды через OpenWeatherMap API.
    
    Args:
        city: Название города (на английском, например "Moscow")
        days: Дней прогноза (1-5, по умолчанию 3)
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Ошибка: установите OPENWEATHER_API_KEY в .env файл"
    
    days = max(1, min(5, int(days) if isinstance(days, str) else days))
    
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric", "lang": "ru"},
            timeout=10
        )
        if response.status_code != 200:
            return f"Ошибка API: код {response.status_code}"
        
        data = response.json()
        lines = [
            f"📍 {data['name']}, {data['sys']['country']}",
            f"🌡️ {data['main']['temp']}°C (ощущается как {data['main']['feels_like']}°C)",
            f"☁️ {data['weather'][0]['description'].capitalize()}",
            f"💨 Ветер: {data['wind']['speed']} м/с"
        ]
        
        lines.append(f"\n📅 Прогноз на {days} дн.: используйте веб-поиск для детального прогноза")
        return "\n".join(lines)
        
    except Exception as e:
        return f"Ошибка погоды: {type(e).__name__}"


# Авто-регистрация инструментов
TOOLS: dict[str, Callable] = {
    name: func for name, func in locals().items()
    if callable(func) and getattr(func, 'is_tool', False)
}


def get_tool_schema(name: str) -> dict:
    """Генерирует JSON Schema для инструмента."""
    func = TOOLS.get(name)
    if not func:
        raise ValueError(f"Инструмент '{name}' не найден")
    
    type_mapping = {int: "integer", float: "number", str: "string", bool: "boolean"}
    parameters = {"type": "object", "properties": {}, "required": []}
    
    sig = inspect.signature(func)
    for pname, param in sig.parameters.items():
        ptype = param.annotation if param.annotation != inspect.Parameter.empty else str
        parameters["properties"][pname] = {
            "type": type_mapping.get(ptype, "string"),
            "description": f"{pname}" + (f" (по умолчанию: {param.default})" if param.default is not inspect.Parameter.empty else "")
        }
        if param.default is inspect.Parameter.empty:
            parameters["required"].append(pname)
    
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": (func.__doc__ or "").strip().split("\n")[0],
            "parameters": parameters
        }
    }