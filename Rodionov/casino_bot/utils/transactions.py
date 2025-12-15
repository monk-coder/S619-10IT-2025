# utils/transactions.py
import logging
from datetime import datetime
from database.models import Transaction, GameHistory
from database.db_handler import DatabaseHandler

logger = logging.getLogger(__name__)


class TransactionManager:
    def __init__(self, db_handler: DatabaseHandler):
        self.db = db_handler

    def add_game_transaction(self, user_id: int, game_type: str, bet: int, win: int, result: str) -> bool:
        """Добавление транзакции игры"""
        try:
            logger.info(f"🎯 TRANSACTION START: user_id={user_id}, game_type={game_type}, bet={bet}, win={win}")

            # Получаем текущий баланс
            current_balance = self.db.get_user_balance(user_id)
            logger.info(f"💰 Баланс ДО: {current_balance}")

            # Обновляем баланс
            logger.info(f"🔄 Обновляем баланс на: {win}")
            success = self.db.update_user_balance(user_id, win)

            if success:
                new_balance = self.db.get_user_balance(user_id)
                logger.info(f"💰 Баланс ПОСЛЕ: {new_balance}")

                # Добавляем запись в историю игр
                game_history = GameHistory(
                    user_id=user_id,
                    game_type=game_type,
                    bet=bet,
                    win=win,
                    result=result
                )

                history_success = self.db.add_game_history(game_history)

                # Добавляем транзакцию
                transaction_type = "game_win" if win > 0 else "game_loss" if win < 0 else "game_draw"
                transaction = Transaction(
                    user_id=user_id,
                    type=transaction_type,
                    amount=win,
                    description=f"{game_type}: {result}"
                )

                transaction_success = self.db.add_transaction(transaction)

                logger.info(f"✅ TRANSACTION COMPLETE: баланс изменился с {current_balance} на {new_balance}")
                return True
            else:
                logger.error("❌ TRANSACTION FAILED: не удалось обновить баланс")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка в add_game_transaction: {e}")
            return False

    def get_user_stats(self, user_id: int) -> dict:
        """Получение статистики пользователя"""
        try:
            game_stats = self.db.get_game_stats(user_id)
            total_games = sum(stats['games'] for stats in game_stats.values())
            total_bet = sum(stats['total_bet'] for stats in game_stats.values())
            total_win = sum(stats['total_win'] for stats in game_stats.values())

            return {
                'total_games': total_games,
                'total_bet': total_bet,
                'total_win': total_win,
                'total_profit': total_win - total_bet,
                'game_stats': game_stats
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики пользователя {user_id}: {e}")
            return {
                'total_games': 0,
                'total_bet': 0,
                'total_win': 0,
                'total_profit': 0,
                'game_stats': {}
            }

    def add_admin_transaction(self, user_id: int, amount: int, description: str) -> bool:
        """Добавление административной транзакции"""
        try:
            transaction = Transaction(
                user_id=user_id,
                type="admin_adjustment",
                amount=amount,
                description=description
            )
            return self.db.add_transaction(transaction)
        except Exception as e:
            logger.error(f"Ошибка добавления админ-транзакции: {e}")
            return False