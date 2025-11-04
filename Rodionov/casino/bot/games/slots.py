import random
from bot.games.base_game import BaseGame, GameResult


class SlotsGame(BaseGame):
    def __init__(self, config, db_session):
        super().__init__('slots', config, db_session)
        self.symbols = config.symbols
        self.payouts = config.payouts

    async def play(self, user_id: int, bet: float) -> GameResult:
        # Проверка ставки
        is_valid, error_msg = await self.validate_bet(user_id, bet)
        if not is_valid:
            return GameResult(success=False, win=False, amount=0, message=error_msg)

        # Генерация результата
        reels = [random.choice(self.symbols) for _ in range(3)]
        result_str = ''.join(reels)

        # Проверка выигрыша
        win_multiplier = self.payouts.get(result_str, 0)
        win_amount = bet * win_multiplier

        # Формирование деталей результата
        result_data = {
            'reels': reels,
            'combination': result_str,
            'multiplier': win_multiplier,
            'win_amount': win_amount
        }

        if win_amount > 0:
            return await self.process_win(user_id, bet, win_amount, result_data)
        else:
            return await self.process_loss(user_id, bet, result_data)