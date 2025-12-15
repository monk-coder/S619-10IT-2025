# games/slots.py
import random
import logging

logger = logging.getLogger(__name__)

class SlotMachine:
    def __init__(self):
        self.symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']

    def play(self, user_id: int, bet: int):
        try:
            # Генерируем результат
            result = [random.choice(self.symbols) for _ in range(3)]

            # Проверяем выигрышные комбинации
            win_multiplier = 0
            description = "❌ Проигрыш"

            if result[0] == result[1] == result[2]:
                # Три одинаковых символа
                if result[0] == '7️⃣':
                    win_multiplier = 10
                    description = "💰 ДЖЕКПОТ! Три семерки! x10"
                elif result[0] == '💎':
                    win_multiplier = 8
                    description = "🎯 Три алмаза! x8"
                elif result[0] == '🔔':
                    win_multiplier = 5
                    description = "🔥 Три колокольчика! x5"
                else:
                    win_multiplier = 3
                    description = "🎉 Три одинаковых! x3"
            elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
                # Два одинаковых символа
                win_multiplier = 2
                description = "✅ Две одинаковые! x2"

            # Рассчитываем ВЫИГРЫШ
            # Чистый выигрыш = (ставка * множитель) - ставка
            total_win = bet * win_multiplier
            net_win = total_win - bet  # ЧИСТЫЙ выигрыш

            logger.info(f"🎰 SLOTS CALC: bet={bet}, multiplier={win_multiplier}, total_win={total_win}, net_win={net_win}")

            return {
                'success': True,
                'final_result': result,
                'win_amount': net_win,  # Возвращаем ЧИСТЫЙ выигрыш
                'description': description,
                'multiplier': win_multiplier,
                'total_win': total_win
            }

        except Exception as e:
            logger.error(f"Ошибка в слотах: {e}")
            return {
                'success': False,
                'error': 'Ошибка игры'
            }