# animations/roulette_animation.py
from .base_animations import BaseAnimation
import random

class RouletteAnimation(BaseAnimation):
    def create_animation(self, winning_number, winning_color, color_emoji):
        """Анимация рулетки с реалистичным вращением"""
        frames = []

        # Запуск рулетки
        frames.append("🎡 *ЗАПУСК РУЛЕТКИ* 🎡\n\nШарик начинает движение...")

        # Вращение
        for i in range(8):
            random_num = random.randint(0, 36)
            random_color = self._get_number_color(random_num)
            speed = "🌀" * min((i // 2) + 1, 3)
            frames.append(f"🎡 *ШАЛИК ВРАЩАЕТСЯ* {speed}\n\n       {random_color} {random_num:2d}")

        # Замедление
        frames.append("🎡 *ШАЛИК ЗАМЕДЛЯЕТСЯ* ⏳\n\nПриготовьтесь к результату...")

        # Финальные числа перед выигрышным
        for i in range(2):
            nearby = (winning_number - 2 + i) % 37
            color = self._get_number_color(nearby)
            frames.append(f"🎡 *ШАЛИК ПРОХОДИТ...* ✨\n\n       {color} {nearby:2d}")

        # Финальный результат
        frames.append(f"🎡 *ШАЛИК ОСТАНОВИЛСЯ!* 🎯\n\n       {color_emoji} {winning_number:2d}")

        return frames

    def _get_number_color(self, number):
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        if number == 0:
            return '🟢'
        elif number in red_numbers:
            return '🔴'
        else:
            return '⚫'