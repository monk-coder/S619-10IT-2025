import requests
from duckduckgo_search import DDGS
import math


def web_search(query: str) -> str:

    try:
        results = []

        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=3)

            for r in search_results:
                results.append(r["body"])

        if not results:
            return "Ничего не найдено"

        return "\n".join(results)

    except Exception as e:
        return f"Ошибка поиска: {e}"


def calculator(expression: str) -> str:

    allowed_names = {
        "abs": abs,
        "round": round,
        "sqrt": math.sqrt
    }

    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)

    except Exception as e:
        return f"Ошибка вычисления: {e}"


def get_weather(city: str) -> str:

    try:
        url = f"https://wttr.in/{city}?format=3"

        response = requests.get(url)

        if response.status_code != 200:
            return "Не удалось получить погоду"

        return response.text

    except Exception as e:
        return f"Ошибка погоды: {e}"