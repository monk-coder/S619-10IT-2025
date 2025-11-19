
# animations/dice_animation.py
from .base_animations import BaseAnimation
import random

class DiceAnimation(BaseAnimation):
    def create_animation(self, player_roll, bot_roll):
        """Реалистичная анимация броска костей"""
        dice_faces = self._get_dice_faces()
        frames = []

        # Подготовка к броску
        frames.append("🎲 *ПОДГОТОВКА К БРОСКУ* 🎲\n\nКости готовы к игре...")

        # Бросок игрока
        frames.append("🎲 *ВАШ БРОСОК* 👤\n\nКости летят по столу...")
        for i in range(3):
            temp_roll = random.randint(1, 6)
            frames.append(f"🎲 *БРОСОК...* 🎯\n\n{dice_faces[temp_roll]}")

        # Результат игрока
        frames.append(f"🎲 *ВАШ РЕЗУЛЬТАТ: {player_roll}* ✅\n\n{dice_faces[player_roll]}")

        # Бросок бота
        frames.append("🎲 *БРОСОК БОТА* 🤖\n\nПротивник делает ход...")
        for i in range(2):
            temp_roll = random.randint(1, 6)
            frames.append(f"🎲 *БОТ БРОСАЕТ...* ⚡\n\n{dice_faces[temp_roll]}")

        # Результат бота
        frames.append(f"🎲 *РЕЗУЛЬТАТ БОТА: {bot_roll}* 🤖\n\n{dice_faces[bot_roll]}")

        # Сравнение результатов
        result_msg = self._get_comparison_result(player_roll, bot_roll)
        frames.append(f"🎲 *ИТОГ ИГРЫ* 🏁\n\n{result_msg}\n\nВы: {player_roll} vs Бот: {bot_roll}")

        return frames

    def _get_dice_faces(self):
        return {
            1: "┌───────┐\n│         │\n│    ●    │\n│         │\n└───────┘",
            2: "┌───────┐\n│    ●    │\n│         │\n│    ●    │\n└───────┘",
            3: "┌───────┐\n│    ●    │\n│    ●    │\n│    ●    │\n└───────┘",
            4: "┌───────┐\n│  ●   ●  │\n│         │\n│  ●   ●  │\n└───────┘",
            5: "┌───────┐\n│  ●   ●  │\n│    ●    │\n│  ●   ●  │\n└───────┘",
            6: "┌───────┐\n│  ●   ●  │\n│  ●   ●  │\n│  ●   ●  │\n└───────┘"
        }

    def _get_comparison_result(self, player_roll, bot_roll):
        if player_roll > bot_roll:
            return "🎉 *ВЫ ВЫИГРАЛИ!* Ваш бросок сильнее!"
        elif player_roll < bot_roll:
            return "😞 *ВЫ ПРОИГРАЛИ* Бот бросил лучше"
        else:
            return "🤝 *НИЧЬЯ!* Одинаковый результат"