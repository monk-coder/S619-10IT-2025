# utils/daily_bonus.py
import logging
from datetime import datetime, timedelta
from database.models import Transaction
from database.db_handler import DatabaseHandler

logger = logging.getLogger(__name__)


class DailyBonus:
    def __init__(self, db_handler: DatabaseHandler):
        self.db = db_handler

    def can_claim_bonus(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь получить ежедневный бонус"""
        try:
            # Получаем последнюю транзакцию бонуса
            transactions = self.db.get_user_transactions(user_id, limit=50)

            for transaction in transactions:
                if transaction.type == 'daily_bonus':
                    # Проверяем, когда был получен последний бонус
                    if transaction.timestamp:
                        last_bonus_date = datetime.fromisoformat(transaction.timestamp.replace('Z', '+00:00')).date()
                        current_date = datetime.now().date()

                        if last_bonus_date == current_date:
                            return False  # Бонус уже получен сегодня
                    break

            return True  # Может получить бонус

        except Exception as e:
            logger.error(f"Ошибка при проверке бонуса для пользователя {user_id}: {e}")
            return True

    def claim_bonus(self, user_id: int) -> dict:
        """Выдача ежедневного бонуса"""
        try:
            if not self.can_claim_bonus(user_id):
                return {
                    'success': False,
                    'message': '❌ Вы уже получали бонус сегодня!\nПриходите завтра! 🗓️'
                }

            bonus_amount = 10

            # Добавляем бонус к балансу
            success = self.db.update_user_balance(user_id, bonus_amount)

            if success:
                # Логируем транзакцию
                transaction = Transaction(
                    user_id=user_id,
                    type='daily_bonus',
                    amount=bonus_amount,
                    description='Ежедневный бонус за вход'
                )
                self.db.add_transaction(transaction)

                # Получаем новый баланс
                new_balance = self.db.get_user_balance(user_id)

                return {
                    'success': True,
                    'message': f'🎉 *Вы получили ежедневный бонус!*\n\n💰 +{bonus_amount} 🪙\n💎 Теперь у вас: {new_balance} 🪙\n\nПриходите завтра за новым бонусом! 🗓️',
                    'amount': bonus_amount,
                    'new_balance': new_balance
                }
            else:
                return {
                    'success': False,
                    'message': '❌ Ошибка при выдаче бонуса'
                }

        except Exception as e:
            logger.error(f"Ошибка при выдаче бонуса пользователю {user_id}: {e}")
            return {
                'success': False,
                'message': '❌ Ошибка при выдаче бонуса'
            }

    def get_bonus_info(self, user_id: int) -> dict:
        """Получить информацию о бонусе"""
        try:
            can_claim = self.can_claim_bonus(user_id)

            if can_claim:
                return {
                    'can_claim': True,
                    'message': '🎁 *Ежедневный бонус доступен!*\n\n💰 Получите +10 🪙 за вход!\n\nИспользуйте команду /daily'
                }
            else:
                # Находим когда был получен последний бонус
                transactions = self.db.get_user_transactions(user_id, limit=50)
                last_bonus_time = None

                for transaction in transactions:
                    if transaction.type == 'daily_bonus':
                        last_bonus_time = transaction.timestamp
                        break

                if last_bonus_time:
                    last_bonus_date = datetime.fromisoformat(last_bonus_time.replace('Z', '+00:00'))
                    next_bonus_time = (last_bonus_date + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                    time_until_next = next_bonus_time - datetime.now()

                    hours_remaining = int(time_until_next.total_seconds() // 3600)
                    minutes_remaining = int((time_until_next.total_seconds() % 3600) // 60)

                    return {
                        'can_claim': False,
                        'message': f'⏳ *Бонус уже получен сегодня*\n\nСледующий бонус через: {hours_remaining}ч {minutes_remaining}м\n\nПриходите завтра! 🗓️',
                        'next_available': next_bonus_time
                    }
                else:
                    return {
                        'can_claim': True,
                        'message': '🎁 *Ежедневный бонус доступен!*\n\n💰 Получите +10 🪙 за вход!'
                    }

        except Exception as e:
            logger.error(f"Ошибка при получении информации о бонусе для пользователя {user_id}: {e}")
            return {
                'can_claim': True,
                'message': '🎁 *Ежедневный бонус доступен!*\n\n💰 Получите +10 🪙 за вход!'
            }