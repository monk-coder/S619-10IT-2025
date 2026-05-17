#!/usr/bin/env python3
"""
Точка входа для ReAct Agent.
"""

import sys
import os
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent import ReActAgent


def setup_encoding() -> None:
    """Настраивает кодировку для корректного вывода кириллицы в Windows."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except:
            pass
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="🤖 ReAct Agent — AI-агент с инструментами",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  %(prog)s "Сколько будет 2 в степени 10?"
  %(prog)s --interactive
  %(prog)s --model mistral "Погода в Лондоне"
  %(prog)s --eval                      # запустить тесты
  %(prog)s --debug "Тестовый вопрос"   # подробный лог
        """
    )
    
    parser.add_argument("question", nargs="?", help="Вопрос для агента")
    parser.add_argument("--model", "-m", type=str, default=None, help="Модель Ollama")
    parser.add_argument("--base-url", "-u", type=str, default=None, help="URL API Ollama")
    parser.add_argument("--max-iter", "-i", type=int, default=10, help="Макс. итераций")
    parser.add_argument("--temp", "-t", type=float, default=0.2, help="Температура: 0.0-1.0")
    parser.add_argument("--quiet", "-q", action="store_true", help="Минимальный вывод")
    parser.add_argument("--debug", "-d", action="store_true", help="Подробный лог")
    parser.add_argument("--interactive", "-I", action="store_true", help="Интерактивный режим")
    parser.add_argument("--eval", "-e", action="store_true", help="Запустить оценку")
    parser.add_argument("--output", "-o", type=str, default=None, help="Сохранить в JSON")
    
    return parser.parse_args()


def print_answer(result: dict, quiet: bool = False) -> None:
    if quiet:
        print(result["answer"])
        return
    
    status_icon = "✅" if result["success"] else "❌"
    print(f"\n{status_icon} Ответ: {result['answer']}")
    print(f"\n📊 Статистика:")
    print(f"   • Итераций: {result['iterations']}")
    print(f"   • Успех: {result['success']}")
    print(f"   • Модель: {result.get('model', 'N/A')}")
    
    if result.get("trace"):
        print(f"\n🔍 Трассировка ({len(result['trace'])} шагов):")
        for i, step in enumerate(result["trace"][:5], 1):
            step_type = step.get("step", "unknown")
            if step_type == "action":
                print(f"   {i}. 🔧 {step.get('tool')}({step.get('arguments')})")
            elif step_type == "final_answer":
                print(f"   {i}. ✅ Final Answer")
            elif step_type == "error":
                print(f"   {i}. ❌ Error: {step.get('error')}")
        if len(result["trace"]) > 5:
            print(f"   ... и ещё {len(result['trace']) - 5} шагов")


def run_interactive(agent: ReActAgent) -> None:
    print(f"\n🤖 ReAct Agent запущен (модель: {agent.model})")
    print("💡 Подсказки: /exit, /quit, /clear, /help")
    print("-" * 60)
    
    while True:
        try:
            prompt = input("\n❓ Вы> ").strip()
            
            if prompt.lower() in ('/exit', '/quit', '/q', 'выход'):
                print("👋 До свидания!")
                break
            
            if prompt.lower() in ('/help', '/h', '?'):
                print("\n📚 Команды: /exit, /quit, /clear, /stats, /model")
                continue
            
            if prompt.lower() == '/clear':
                print("🗑️  История очищена")
                continue
            
            if prompt.lower() == '/stats':
                print(f"\n📊 Сессия: вопросов обработано")
                continue
            
            if prompt.lower() == '/model':
                print(f"🤖 Модель: {agent.model}")
                continue
            
            if not prompt:
                continue
            
            print("\n🔄 Думаю...")
            result = agent.run(prompt)
            print_answer(result, quiet=agent.verbose)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Прервано. Введите /exit для выхода.")
        except EOFError:
            break


def run_evaluation() -> bool:
    print("🧪 Запуск автоматической оценки...\n")
    try:
        from evaluate import main as evaluate_main
        return evaluate_main()
    except ImportError:
        print("❌ Не удалось импортировать evaluate.py")
        return False
    except Exception as e:
        print(f"❌ Ошибка при оценке: {e}")
        return False


def main() -> int:
    setup_encoding()
    args = parse_args()
    
    if args.eval:
        return 0 if run_evaluation() else 1
    
    agent = ReActAgent(
        model=args.model,
        base_url=args.base_url,
        max_iterations=args.max_iter,
        verbose=not args.quiet and not args.debug,
        temperature=args.temp
    )
    
    if args.interactive or not args.question:
        run_interactive(agent)
        return 0
    
    result = agent.run(args.question)
    print_answer(result, quiet=args.quiet)
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 Результат сохранён в {args.output}")
        except IOError as e:
            print(f"❌ Не удалось сохранить: {e}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())