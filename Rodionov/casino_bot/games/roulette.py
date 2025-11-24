# games/roulette.py
import random
import logging

logger = logging.getLogger(__name__)

class RouletteGame:
    def __init__(self):
        self.numbers = list(range(0, 37))  # 0-36
        self.red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        self.black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

    def play(self, user_id: int, bet_type: str, bet_value: str, bet_amount: int):
        try:
            winning_number = random.choice(self.numbers)

            # Определяем цвет выигрышного числа
            if winning_number == 0:
                color = 'green'
                color_emoji = '🟢'
            elif winning_number in self.red_numbers:
                color = 'red'
                color_emoji = '🔴'
            else:
                color = 'black'
                color_emoji = '⚫'

            # Проверяем выигрыш
            is_win = self.check_win(bet_type, bet_value, winning_number, color)

            # Рассчитываем выплату
            if is_win:
                multiplier = self.get_multiplier(bet_type)
                total_win = bet_amount * multiplier
                net_win = total_win - bet_amount  # ЧИСТЫЙ выигрыш
            else:
                net_win = -bet_amount  # ЧИСТЫЙ проигрыш

            winning_result = {
                'number': winning_number,
                'color': color,
                'color_emoji': color_emoji
            }

            return {
                'success': True,
                'is_win': is_win,
                'winning_result': winning_result,
                'payout': net_win,  # Возвращаем ЧИСТЫЙ выигрыш/проигрыш
                'net_profit': net_win,
                'multiplier': multiplier if is_win else 0
            }

        except Exception as e:
            logger.error(f"Ошибка в рулетке: {e}")
            return {
                'success': False,
                'error': 'Ошибка игры'
            }

    def check_win(self, bet_type, bet_value, winning_number, winning_color):
        """Проверка выигрышной комбинации"""
        logger.info(f"🎯 Проверка выигрыша: type={bet_type}, value={bet_value}, win_num={winning_number}, win_color={winning_color}")

        if bet_type == 'color':
            return bet_value == winning_color
        elif bet_type == 'even_odd':
            if bet_value == 'even':
                return winning_number % 2 == 0 and winning_number != 0
            else:  # odd
                return winning_number % 2 == 1 and winning_number != 0
        elif bet_type == 'specific':
            return int(bet_value) == winning_number
        elif bet_type == 'dozen':
            dozen = int(bet_value)
            if dozen == 1:
                return 1 <= winning_number <= 12
            elif dozen == 2:
                return 13 <= winning_number <= 24
            elif dozen == 3:
                return 25 <= winning_number <= 36
        return False

    def get_multiplier(self, bet_type):
        """Получение множителя для типа ставки"""
        multipliers = {
            'color': 2,
            'even_odd': 2,
            'specific': 36,
            'dozen': 3
        }
        return multipliers.get(bet_type, 1)