import re
import ast
import operator
import requests
import os
import inspect
from duckduckgo_search import DDGS
from collections import defaultdict

def tool(func):
    func.is_tool = True
    return func

@tool
def web_search(query: str, max_results: int = 3) -> str:
    """Поиск информации в интернете."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"• {r.get('title', '')}: {r.get('body', '')}")
        return "\n".join(results) if results else "Ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"

@tool
def calculator(expression: str) -> str:
    """Безопасное вычисление математических выражений."""
    ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg,
    }
    def _eval(node):
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.BinOp): return ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp): return ops[type(node.op)](_eval(node.operand))
        raise ValueError("Неподдерживаемый элемент")
    
    try:
        if not re.match(r'^[\d\s\+\-\*\/\%\.\(\)\*\*]+$', expression.strip()):
            return "Ошибка: недопустимые символы"
        result = _eval(ast.parse(expression.strip(), mode='eval').body)
        return str(int(result)) if isinstance(result, float) and result.is_integer() else f"{result:.2f}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

@tool
def get_weather(city: str, days: int = 3) -> str:
    """Прогноз погоды."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key: return "Ошибка: нет OPENWEATHER_API_KEY в .env"
    
    try:
        # Текущая погода
        r = requests.get("http://api.openweathermap.org/data/2.5/weather", 
                         params={"q": city, "appid": api_key, "units": "metric", "lang": "ru"}, timeout=10)
        if r.status_code != 200: return f"Ошибка API: {r.status_code}"
        d = r.json()
        
        lines = [
            f"📍 {d['name']}, {d['sys']['country']}",
            f"🌡️ {d['main']['temp']}°C (ощущается {d['main']['feels_like']}°C)",
            f"☁️ {d['weather'][0]['description']}, 💨 {d['wind']['speed']} м/с"
        ]
        
        # Прогноз
        r_f = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                           params={"q": city, "appid": api_key, "units": "metric", "cnt": days*8}, timeout=10)
        if r_f.status_code == 200:
            daily = defaultdict(list)
            for item in r_f.json()['list']:
                daily[item['dt_txt'].split()[0]].append(item['main']['temp'])
            lines.append("\n📅 Прогноз:")
            for dt, temps in list(daily.items())[:days]:
                lines.append(f"  {dt}: ~{sum(temps)/len(temps):.1f}°C")
        return "\n".join(lines)
    except Exception as e:
        return f"Ошибка: {str(e)}"

TOOLS = {n: f for n, f in locals().items() if hasattr(f, 'is_tool')}

def get_tool_schema(name):
    func = TOOLS.get(name)
    if not func: raise ValueError(f"Нет тула {name}")
    params = {"type": "object", "properties": {}, "required": []}
    sig = inspect.signature(func)
    for pname, p in sig.parameters.items():
        params["properties"][pname] = {"type": "string"}
        if p.default is inspect.Parameter.empty: params["required"].append(pname)
    return {
        "type": "function",
        "function": {"name": name, "description": (func.__doc__ or "").strip(), "parameters": params}
    }
