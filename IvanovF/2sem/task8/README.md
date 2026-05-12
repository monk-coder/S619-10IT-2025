# ReAct Agent

## Установка

```bash
ollama pull llama3.2:1b
```

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python agent.py
```

```bash
python evaluate.py
```

## Пример

```text
Question: Какая погода в Барселоне?

Thought: Нужно узнать погоду.
Action: get_weather["Барселона"]

Observation: Barcelona: +18°C

Final Answer: В Барселоне +18°C
```