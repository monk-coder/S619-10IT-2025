# animations/slots_animation.py
from .base_animations import BaseAnimation
import random

class SlotsAnimation(BaseAnimation):
    def create_animation(self, final_result):
        """Анимация слотов с реалистичными эффектами"""
        symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
        frames = []

        # Запуск машины
        frames.append("🎰 *ЗАПУСК АВТОМАТА* 🎰\n\nИнициализация системы...")

        # Быстрое вращение
        for i in range(6):
            speed = min(i + 1, 5)
            random_symbols = [random.choice(symbols) for _ in range(3)]
            frames.append(
                f"🎰 *БАРАБАНЫ ВРАЩАЮТСЯ* {'🌀' * speed}\n\n"
                f"       {random_symbols[0]}   {random_symbols[1]}   {random_symbols[2]}"
            )

        # Замедление первого барабана
        frames.append(f"🎰 *ПЕРВЫЙ БАРАБАН ОСТАНАВЛИВАЕТСЯ* ⏳\n\n       {final_result[0]}   🎡   🎡")

        # Замедление второго барабана
        frames.append(f"🎰 *ВТОРОЙ БАРАБАН ОСТАНАВЛИВАЕТСЯ* ⏳\n\n       {final_result[0]}   {final_result[1]}   🎡")

        # Финальный барабан с напряжением
        frames.append(f"🎰 *ФИНАЛЬНЫЙ БАРАБАН...* 💫\n\n       {final_result[0]}   {final_result[1]}   {final_result[2]}")

        return frames