from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional
from bot.database.operations import UserOperations, GameOperations


@dataclass
class GameResult:
    success: bool
    win: bool
    amount: float
    message: str
    details: Optional[dict] = None


class BaseGame(ABC):
    def __init__(self, game_type: str, config, db_session):
        self.game_type = game_type
        self.config = config
        self.user_ops = UserOperations(db_session)
        self.game_ops = GameOperations(db_session)

    async def validate_bet(self, user_id: int, bet: float) -> Tuple[bool, str]:
        """Проверка ставки"""
        if bet < self.config.min_bet:
            return False, f"Минимальная ставка: {self.config.min_bet} монет"

        if bet > self.config.max_bet:
            return False, f"Максимальная ставка: {self.config.max_bet} монет"

        balance = await self.user_ops.get_balance(user_id)
        if bet > balance:
            return False, "Недостаточно средств на балансе"

        return True, ""

    async def process_win(self, user_id: int, bet: float, win_amount: float, result_data: dict = None) -> GameResult:
        """Обработка выигрыша"""
        net_win = win_amount - bet

        # Обновляем баланс
        await self.user_ops.update_balance(user_id, net_win)

        # Сохраняем запись об игре
        await self.game_ops.add_game_record(
            user_id=user_id,
            game_type=self.game_type,
            bet_amount=bet,
            win_amount=win_amount,
            result_data=result_data
        )

        return GameResult(
            success=True,
            win=True,
            amount=net_win,
            message=f"🎉 Поздравляем! Вы выиграли {win_amount} монет!",
            details=result_data
        )

    async def process_loss(self, user_id: int, bet: float, result_data: dict = None) -> GameResult:
        """Обработка проигрыша"""
        # Обновляем баланс
        await self.user_ops.update_balance(user_id, -bet)

        # Сохраняем запись об игре
        await self.game_ops.add_game_record(
            user_id=user_id,
            game_type=self.game_type,
            bet_amount=bet,
            win_amount=0,
            result_data=result_data
        )

        return GameResult(
            success=True,
            win=False,
            amount=-bet,
            message=f"😔 К сожалению, вы проиграли {bet} монет",
            details=result_data
        )

    @abstractmethod
    async def play(self, user_id: int, bet: float, **kwargs) -> GameResult:
        """Основной метод игры"""
        pass