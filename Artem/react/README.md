# 🤖 ReAct Agent с инструментами

Локальный LLM-агент, реализующий паттерн ReAct (Reasoning + Acting). Самостоятельно выбирает инструменты, рассуждает и выполняет многошаговые задачи.

# Инструкция по запуску

### 1. Клонирование проекта
```bash
git clone https://github.com/ВАШ_НИК/react-agent.git
cd react-agent

python -m venv venv

# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

3. Установка и настройка Ollama ⚠️ ОБЯЗАТЕЛЬНО
Агент работает локально через Ollama. Без него тесты не пройдут.
Скачайте Ollama: https://ollama.com/download
Windows: запустите .exe установщик
macOS: перетащите в Applications
Linux: curl -fsSL https://ollama.com/install.sh | sh
Запустите приложение (оно должно висеть в трее/фоне)
Скачайте модель в терминале:
ollama pull llama3.2:latest

4. Настройка API-ключей
Скопируйте шаблон:
cp .env.example .env   # Windows: copy .env.example .env

5. Запуск тестов
python evaluate.py
