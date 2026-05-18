import requests
import json
import math
import re
from duckduckgo_search import DDGS

def web_search(query: str, max_results=3) -> str:
    """Поиск информации в интернете через DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "Не удалось найти результаты."
            snippets = [f"{r['title']}: {r['body']}" for r in results]
            return "\n".join(snippets)
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"

def calculator(expression: str) -> str:
    """Вычисление математического выражения. Поддерживает + - * / ** % и функции math."""
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names.update({"abs": abs, "round": round})
    if re.search(r"[^0-9a-zA-Z+\-*/%()., ]", expression):
        return "Ошибка: выражение содержит недопустимые символы."
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Ошибка вычисления: {str(e)}"

def get_weather(city: str) -> str:
    """Получение погоды в городе через wttr.in"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current_condition", [{}])[0]
            temp = current.get("temp_C", "N/A")
            desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
            return f"В {city} сейчас {temp}°C, {desc}"
        else:
            return f"Не удалось получить погоду для {city}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

def currency_converter(amount: float, from_currency: str, to_currency: str) -> str:
    """Конвертация валюты через exchangerate.host (без ключа)"""
    try:
        url = f"https://api.exchangerate.host/convert?from={from_currency.upper()}&to={to_currency.upper()}&amount={amount}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = data.get("result")
            if result is not None:
                return f"{amount} {from_currency.upper()} = {result:.2f} {to_currency.upper()}"
            else:
                return "Ошибка конвертации"
        else:
            return "Ошибка API курса валют"
    except Exception as e:
        return f"Ошибка: {str(e)}"