"""
Инструменты для ReAct Agent.
Каждый инструмент — функция с декоратором @tool для регистрации.
"""
import re
import ast
import operator
import requests
import os
from typing import Callable, Dict
from duckduckgo_search import DDGS


def tool(func: Callable) -> Callable:
    """Декоратор для регистрации инструментов."""
    func.is_tool = True
    return func


@tool
def web_search(query: str, max_results: int = 3) -> str:
    """
    Поиск информации в интернете через DuckDuckGo.
    
    Args:
        query: Поисковый запрос
        max_results: Максимальное количество результатов (по умолчанию 3)
    
    Returns:
        Строка с заголовками и сниппетами результатов
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get('title', 'No title')
                snippet = r.get('body', 'No snippet')
                href = r.get('href', '')
                results.append(f"• {title}: {snippet} [{href}]")
        
        if not results:
            return "Ничего не найдено по запросу."
        return "\n".join(results)
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"


@tool
def calculator(expression: str) -> str:
    """
    Безопасное вычисление математических выражений.
    
    Поддерживает: +, -, *, /, **, %, (), числа с плавающей точкой.
    НЕ поддерживает: eval, exec, импорт, вызов функций.
    
    Args:
        expression: Математическое выражение как строка
    
    Returns:
        Результат вычисления или сообщение об ошибке
    """
    # Разрешённые операторы
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,  # унарный минус
    }
    
    def _eval_node(node):
        if isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Только числа разрешены")
        elif isinstance(node, ast.Num):  # Python <3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Оператор {op_type} не разрешён")
            return operators[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Оператор {op_type} не разрешён")
            return operators[op_type](operand)
        else:
            raise ValueError(f"Неподдерживаемый элемент: {type(node)}")
    
    try:
        # Очистка выражения от лишних символов
        expr = expression.strip()
        if not re.match(r'^[\d\s\+\-\*\/\%\.\(\)\*\*]+$', expr):
            return "Ошибка: выражение содержит недопустимые символы"
        
        tree = ast.parse(expr, mode='eval')
        result = _eval_node(tree.body)
        
        # Форматирование результата
        if isinstance(result, float):
            if result == int(result):
                return str(int(result))
            return f"{result:.4f}".rstrip('0').rstrip('.')
        return str(result)
    except ZeroDivisionError:
        return "Ошибка: деление на ноль"
    except SyntaxError:
        return "Ошибка: неверный синтаксис выражения"
    except ValueError as e:
        return f"Ошибка: {str(e)}"
    except Exception as e:
        return f"Неизвестная ошибка: {str(e)}"


@tool
def get_weather(city: str, days: int = 3) -> str:
    """
    Получение прогноза погоды через OpenWeatherMap API.
    
    Args:
        city: Название города (на английском или с кодом страны, напр. "Moscow,ru")
        days: Количество дней прогноза (1-5, по умолчанию 3)
    
    Returns:
        Строка с прогнозом погоды
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Ошибка: OPENWEATHER_API_KEY не настроен в .env"
    
    try:
        # Текущая погода
        current_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "ru"
        }
        resp = requests.get(current_url, params=params, timeout=10)
        if resp.status_code != 200:
            return f"Ошибка API: {resp.status_code} — {resp.text}"
        
        data = resp.json()
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind = data['wind']['speed']
        
        result = [f"📍 {data['name']}, {data['sys']['country']}"]
        result.append(f"🌡️ Сейчас: {temp}°C (ощущается как {feels_like}°C)")
        result.append(f"☁️ {desc.capitalize()}, влажность: {humidity}%")
        result.append(f"💨 Ветер: {wind} м/с")
        
        # Прогноз на несколько дней (если доступно)
        forecast_url = "http://api.openweathermap.org/data/2.5/forecast"
        params["cnt"] = days * 8  # 8 запросов на день (каждые 3 часа)
        resp = requests.get(forecast_url, params=params, timeout=10)
        
        if resp.status_code == 200:
            forecast = resp.json()
            result.append("\n📅 Прогноз:")
            # Группируем по дням
            from collections import defaultdict
            daily = defaultdict(list)
            for item in forecast['list']:
                date = item['dt_txt'].split()[0]
                temp_f = item['main']['temp']
                daily[date].append(temp_f)
            
            for date, temps in list(daily.items())[:days]:
                avg = sum(temps) / len(temps)
                result.append(f"  {date}: ~{avg:.1f}°C")
        
        return "\n".join(result)
    
    except requests.Timeout:
        return "Ошибка: тайм-аут запроса к погодному сервису"
    except requests.RequestException as e:
        return f"Ошибка сети: {str(e)}"
    except KeyError as e:
        return f"Ошибка парсинга ответа: отсутствует поле {e}"
    except Exception as e:
        return f"Неизвестная ошибка: {str(e)}"


# Реестр инструментов для быстрого доступа
TOOLS: Dict[str, Callable] = {
    name: func for name, func in locals().items()
    if hasattr(func, 'is_tool') and func.is_tool
}


def get_tool_schema(name: str) -> Dict:
    """Возвращает схему инструмента для Ollama tool calling."""
    func = TOOLS.get(name)
    if not func:
        raise ValueError(f"Инструмент '{name}' не найден")
    
    # Парсинг docstring для описания
    doc = func.__doc__ or ""
    description = doc.split('\n')[0].strip() if doc else ""
    
    # Параметры (упрощённо — все инструменты принимают строки)
    params = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    import inspect
    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if param_name in ('max_results', 'days'):  # опциональные параметры
            params["properties"][param_name] = {
                "type": "integer",
                "description": f"Опциональный параметр: {param_name}"
            }
        else:
            params["properties"][param_name] = {
                "type": "string",
                "description": f"Параметр: {param_name}"
            }
            params["required"].append(param_name)
    
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": params
        }
    }