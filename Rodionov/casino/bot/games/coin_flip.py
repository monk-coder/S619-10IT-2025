import random
from bot.games.base_game import BaseGame, GameResult


class CoinFlipGame(BaseGame):
    def __init__(self, config, db_session):
        super().__init__('coin_flip', config, db_session)

    async def play(self, user_id: int, bet: float, choice: str) -> GameResult:
        # Проверка ставки
        is_valid, error_msg = await self.validate_bet(user_id, bet)
        if not is_valid:
            return GameResult(success=False, win=False, amount=0, message=error_msg)

        # Валидация выбора
        choice = choice.lower()
        if choice not in ['орёл', 'орел', 'решка']:
            return GameResult(
                success=False,
                win=False,
                amount=0,
                message="❌ Неверный выбор. Используйте 'орёл' или 'решка'"
            )

        # Нормализация выбора
        if choice in ['орёл', 'орел']:
            choice = 'орёл'
        else:
            choice = 'решка'

        # Подбрасывание монетки
        result = random.choice(['орёл', 'решка'])

        # Формирование деталей результата
        result_data = {
            'user_choice': choice,
            'result': result,
            'win': choice == result
        }

        if choice == result:
            win_amount = bet * 2
            return await self.process_win(user_id, bet, win_amount, result_data)
        else:
            return await self.process_loss(user_id, bet, result_data)