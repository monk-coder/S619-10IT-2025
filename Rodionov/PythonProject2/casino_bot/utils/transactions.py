# utils/transactions.py
import logging
from typing import Dict
from database.models import GameHistory, Transaction

logger = logging.getLogger(__name__)


class TransactionManager:
    def __init__(self, db_handler):
        self.db = db_handler

    def add_game_transaction(self, user_id: int, game_type: str, bet: int, win: int, result: str):
        """Добавление транзакции для игры - УПРОЩЕННАЯ И РАБОЧАЯ ВЕРСИЯ"""
        try:
            logger.info(f"🎯 TRANSACTION START: user_id={user_id}, game_type={game_type}, bet={bet}, win={win}")

            # Получаем баланс ДО операции
            balance_before = self.db.get_user_balance(user_id)
            logger.info(f"💰 Баланс ДО: {balance_before}")

            # ВАЖНО: win - это ЧИСТЫЙ ВЫИГРЫШ
            # Если win > 0 - выигрыш, если win < 0 - проигрыш

            # ПРОСТАЯ ЛОГИКА: обновляем баланс на сумму чистого выигрыша
            logger.info(f"🔄 Обновляем баланс на: {win}")

            # Используем прямое обновление баланса
            success = self.db.update_user_balance_direct(user_id, win)

            if not success:
                logger.error("❌ Не удалось обновить баланс")
                return False

            # Получаем баланс ПОСЛЕ операции
            balance_after = self.db.get_user_balance(user_id)
            logger.info(f"💰 Баланс ПОСЛЕ: {balance_after}")

            # Логируем игру в историю
            # Для истории храним общий выигрыш (чистый выигрыш + ставка)
            total_win_amount = win + bet if win > 0 else 0

            game_history = GameHistory(
                user_id=user_id,
                game_type=game_type,
                bet=bet,
                win=total_win_amount,
                result=result
            )
            self.db.add_game_history(game_history)

            # Логируем транзакцию
            transaction_type = "win" if win > 0 else "loss"
            transaction = Transaction(
                user_id=user_id,
                type=transaction_type,
                amount=abs(win),
                description=f"{game_type}: {result} (ставка: {bet})"
            )
            self.db.add_transaction(transaction)

            logger.info(f"✅ TRANSACTION COMPLETE: баланс изменился с {balance_before} на {balance_after}")
            return True

        except Exception as e:
            logger.error(f"💥 TRANSACTION ERROR: {e}")
            return False

    def get_user_stats(self, user_id: int) -> Dict:
        """Получение статистики пользователя"""
        try:
            history = self.db.get_user_game_history(user_id, limit=1000)

            total_games = len(history)
            total_wins = sum(1 for game in history if game.win > game.bet)
            total_bet = sum(game.bet for game in history)
            total_win = sum(game.win for game in history)

            win_rate = (total_wins / total_games * 100) if total_games > 0 else 0

            return {
                'total_games': total_games,
                'total_wins': total_wins,
                'win_rate': win_rate,
                'total_bet': total_bet,
                'total_win': total_win,
                'net_profit': total_win - total_bet
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики пользователя {user_id}: {e}")
            return {
                'total_games': 0,
                'total_wins': 0,
                'win_rate': 0,
                'total_bet': 0,
                'total_win': 0,
                'net_profit': 0
            }