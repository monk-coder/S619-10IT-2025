"""
Инструменты для ReAct Agent.
Каждый инструмент — функция с декоратором @tool и docstring для LLM.
"""
import re
import operator
import requests
from typing import Callable, Dict
from duckduckgo_search import DDGS
from dotenv import load_dotenv
import os

load_dotenv()

# Регистрация инструментов
TOOLS: Dict[str, Callable] = {}

def tool(func: Callable) -> Callable:
    """Декоратор для регистрации инструментов."""
    TOOLS[func.__name__] = func
    return func

@tool
def web_search(query: str, max_results: int = 3) -> str:
    """
    Поиск информации в интернете через DuckDuckGo.
    
    Args:
        query: Поисковый запрос
        max_results: Максимальное количество результатов (1-5)
    
    Returns:
        Строка с заголовками и сниппетами результатов
    """
    try:
        max_results = min(max(1, max_results), 5)
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get('title', 'No title')
                snippet = r.get('body', 'No snippet')[:200]
                href = r.get('href', '')
                results.append(f"[{title}]({href}): {snippet}")
        return "\n\n".join(results) if results else "Результаты не найдены."
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"

@tool
def calculator(expression: str) -> str:
    """
    Вычисление математических выражений.
    Поддерживает: +, -, *, /, **, %, (), числа с плавающей точкой.
    
    ⚠️ Безопасная реализация — БЕЗ eval!
    
    Args:
        expression: Математическое выражение, например "15000 + 8000 * 0.1"
    
    Returns:
        Результат вычисления или сообщение об ошибке
    """
    try:
        # Очистка выражения
        expr = expression.strip()
        
        # Разрешённые символы: цифры, точки, операторы, скобки, пробелы
        if not re.match(r'^[\d\s\.\+\-\*\/\%\(\)\*\*]+$', expr):
            return "Ошибка: выражение содержит недопустимые символы"
        
        # Безопасные операторы
        ops = {
            '+': operator.add, '-': operator.sub,
            '*': operator.mul, '/': operator.truediv,
            '%': operator.mod, '**': operator.pow
        }
        
        # Парсинг и вычисление (упрощённый — для сложных выражений можно использовать ast)
        # Для надёжности используем ast.literal_eval + рекурсивный парсинг
        import ast
        
        def eval_node(node):
            if isinstance(node, ast.Constant):  # Python 3.8+
                return node.value
            elif isinstance(node, ast.Num):  # Python <3.8
                return node.n
            elif isinstance(node, ast.BinOp):
                left = eval_node(node.left)
                right = eval_node(node.right)
                op_type = type(node.op)
                if op_type in {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow}:
                    op = ops[{ast.Add: '+', ast.Sub: '-', ast.Mult: '*', 
                             ast.Div: '/', ast.Mod: '%', ast.Pow: '**'}[op_type]]
                    return op(left, right)
                raise ValueError(f"Неподдерживаемая операция: {op_type}")
            elif isinstance(node, ast.UnaryOp):
                operand = eval_node(node.operand)
                if isinstance(node.op, ast.USub):
                    return -operand
                elif isinstance(node.op, ast.UAdd):
                    return operand
                raise ValueError(f"Неподдерживаемый унарный оператор")
            elif isinstance(node, ast.Expression):
                return eval_node(node.body)
            else:
                raise ValueError(f"Неподдерживаемый узел: {type(node)}")
        
        tree = ast.parse(expr, mode='eval')
        result = eval_node(tree.body)
        
        # Форматирование результата
        if isinstance(result, float):
            return str(round(result, 2)) if result != int(result) else str(int(result))
        return str(result)
        
    except SyntaxError:
        return "Ошибка: неверный синтаксис выражения"
    except ZeroDivisionError:
        return "Ошибка: деление на ноль"
    except Exception as e:
        return f"Ошибка вычисления: {str(e)}"

@tool
def get_weather(city: str, days: int = 3) -> str:
    """
    Погода в городе на ближайшие дни через wttr.in (без API ключа).
    
    Args:
        city: Название города (на русском или английском)
        days: Количество дней прогноза (1-3)
    
    Returns:
        Прогноз погоды в читаемом формате
    """
    try:
        days = min(max(1, days), 3)
        # wttr.in поддерживает русский язык через параметр ?lang=ru
        city_encoded = requests.utils.quote(city)
        url = f"https://wttr.in/{city_encoded}?format=j1&lang=ru"
        
        response = requests.get(url, timeout=10, headers={'User-Agent': 'ReAct-Agent/1.0'})
        response.raise_for_status()
        data = response.json()
        
        if 'current_condition' not in data or 'weather' not in data:
            return f"Не удалось получить прогноз для '{city}'"
        
        current = data['current_condition'][0]
        output = [f"📍 {city} — сейчас: {current.get('temp_C', 'N/A')}°C, {current.get('lang_ru', [{}])[0].get('weatherDesc', [{}])[0].get('value', current.get('weatherDesc', [{}])[0].get('value', 'N/A'))}"]
        
        for i, day in enumerate(data['weather'][:days]):
            date = day.get('date', 'N/A')
            max_t = day.get('maxtempC', 'N/A')
            min_t = day.get('mintempC', 'N/A')
            desc = day.get('lang_ru', [{}])[0].get('weatherDesc', [{}])[0].get('value', 'N/A')
            output.append(f"🗓️ {date}: {min_t}°C...{max_t}°C, {desc}")
        
        return "\n".join(output)
        
    except requests.Timeout:
        return "Ошибка: тайм-аут при запросе погоды"
    except requests.ConnectionError:
        return "Ошибка: нет соединения с сервисом погоды"
    except Exception as e:
        return f"Ошибка получения погоды: {str(e)}"

def get_tool_schema(name: str) -> dict:
    """Возвращает схему инструмента для промпта."""
    func = TOOLS.get(name)
    if not func:
        return {}
    doc = func.__doc__ or ""
    return {
        "name": name,
        "description": doc.split('\n\n')[0] if '\n\n' in doc else doc.split('\n')[0],
        "parameters": "См. docstring функции"
    }

def list_tools() -> str:
    """Возвращает список доступных инструментов для промпта."""
    lines = ["Доступные инструменты:"]
    for name, func in TOOLS.items():
        desc = (func.__doc__ or "").split('\n')[0].strip()
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)
