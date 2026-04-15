# 🤖 ReAct Agent (Local CPU)

Агент с циклом **Reasoning + Acting**, работающий полностью локально через **Ollama + llama3.2:1b**.

## ✨ Возможности

- 🔍 Поиск в интернете (DuckDuckGo)
- 🧮 Математические вычисления (безопасный parser)
- 🌤️ Прогноз погоды (wttr.in, без API-ключа)
- 🔄 ReAct-цикл: Thought → Action → Observation
- 🛡️ Защита от бесконечных циклов (`max_iterations=10`)
- 🐛 Обработка ошибок инструментов

## 🚀 Установка

1. **Установите Ollama**: https://ollama.ai

2. **Скачайте модель**:
   ```bash
   ollama pull llama3.2:1b
