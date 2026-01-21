FREE_MODELS = [
    {
        "name": "DeepSeek V3",
        "id": "deepseek/deepseek-chat",
        "description": "Мощная модель для различных задач"
    },
    {
        "name": "DeepSeek R1",
        "id": "deepseek/deepseek-r1",
        "description": "Улучшенная модель с рассуждениями"
    },
    {
        "name": "Qwen 3 Coder",
        "id": "qwen/qwen3-coder:free",
        "description": "Специализирована на программировании"
    },
    {
        "name": "Llama 3.3 70B",
        "id": "meta-llama/llama-3.3-70b-instruct:free",
        "description": "Большая универсальная модель от Meta ∆"
    }
]


def get_model_name_by_id(model_id: str) -> str:
    for model in FREE_MODELS:
        if model["id"] == model_id:
            return model["name"]
    return model_id
