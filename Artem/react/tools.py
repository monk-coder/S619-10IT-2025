import re
import ast
import operator
import requests
import os
import inspect
from duckduckgo_search import DDGS


def tool(func):
    """Декоратор для регистрации инструментов."""
    func.is_tool = True
    return func


@tool
def web_search(query: str, max_results: int = 3) -> str:
    """Поиск информации в интернете через DuckDuckGo."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get('title', 'No title')
                snippet = r.get('body', 'No snippet')
                href = r.get('href', '')
                results.append(f"• {title}: {snippet} [{href}]")
        return "\n".join(results) if results else "Ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"


@tool
def calculator(expression: str) -> str:
    """Безопасное вычисление математических выражений (+, -, *, /, **, %)."""
    operators = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg,
    }
    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)): return node.value
            raise ValueError("Только числа")
        if isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        raise ValueError(f"Неподдерживаемый элемент: {type(node)}")
    try:
        if not re.match(r'^[\d\s\+\-\*\/\%\.\(\)\*\*]+$', expression.strip()):
            return "Ошибка: недопустимые символы"
        result = _eval(ast.parse(expression.strip(), mode='eval').body)
        return str(int(result)) if isinstance(result, float) and result.is_integer() else f"{result:.4f}".rstrip('0').rstrip('.')
    except ZeroDivisionError:
        return "Ошибка: деление на ноль"
    except Exception as e:
        return f"Ошибка вычисления: {str(e)}"


@tool
def get_weather(city: str, days: int = 3) -> str:
    """Прогноз погоды через OpenWeatherMap API."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Ошибка: OPENWEATHER_API_KEY не задан в .env"
    try:
        resp = requests.get("http://api.openweathermap.org/data/2.5/weather", 
                            params={"q": city, "appid": api_key, "units": "metric", "lang": "ru"}, timeout=10)
        if resp.status_code != 200:
            return f"Ошибка API: {resp.status_code}"
        data = resp.json()
        lines = [
            f" {data['name']}, {data['sys']['country']}",
            f"️ Сейчас: {data['main']['temp']}°C (ощущается {data['main']['feels_like']}°C)",
            f"☁️ {data['weather'][0]['description'].capitalize()}, влажность {data['main']['humidity']}%",
            f"💨 Ветер: {data['wind']['speed']} м/с"
        ]
        # Прогноз
        f_resp = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                              params={"q": city, "appid": api_key, "units": "metric", "cnt": days*8}, timeout=10)
        if f_resp.status_code == 200:
            from collections import defaultdict
            daily = defaultdict(list)
            for item in f_resp.json()['list']:
                daily[item['dt_txt'].split()[0]].append(item['main']['temp'])
            lines.append("\n📅 Прогноз:")
            for d, temps in list(daily.items())[:days]:
                lines.append(f"  {d}: ~{sum(temps)/len(temps):.1f}°C")
        return "\n".join(lines)
    except Exception as e:
        return f"Ошибка погоды: {str(e)}"


# Реестр инструментов
TOOLS = {name: func for name, func in locals().items() if hasattr(func, 'is_tool')}


def get_tool_schema(name: str) -> dict:
    """Возвращает JSON-схему инструмента для Ollama."""
    func = TOOLS.get(name)
    if not func: raise ValueError(f"Инструмент '{name}' не найден")
    params = {"type": "object", "properties": {}, "required": []}
    sig = inspect.signature(func)
    for pname, param in sig.parameters.items():
        params["properties"][pname] = {"type": "string", "description": f"Параметр: {pname}"}
        if param.default is inspect.Parameter.empty:
            params["required"].append(pname)
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": (func.__doc__ or "").split('\n')[0].strip(),
            "parameters": params
        }
    }
