# games/dice.py
import random
import logging

logger = logging.getLogger(__name__)

class DiceGame:
    def play(self, user_id: int, bet: int):
        try:
            player_roll = random.randint(1, 6)
            bot_roll = random.randint(1, 6)

            logger.info(f"🎯 DICE ROLL: user_id={user_id}, player={player_roll}, bot={bot_roll}")

            if player_roll > bot_roll:
                # Игрок выиграл - получает удвоенную ставку
                total_win = bet * 2
                net_win = total_win - bet  # ЧИСТЫЙ выигрыш
                description = f"🎉 Вы выиграли! {player_roll} > {bot_roll}"
                logger.info(f"✅ PLAYER WINS: bet={bet}, total_win={total_win}, net_win={net_win}")
            elif player_roll < bot_roll:
                # Игрок проиграл - теряет ставку
                net_win = -bet  # ЧИСТЫЙ проигрыш
                description = f"❌ Вы проиграли! {player_roll} < {bot_roll}"
                logger.info(f"❌ PLAYER LOSES: bet={bet}, net_win={net_win}")
            else:
                # Ничья - возврат ставки
                net_win = 0
                description = f"🤝 Ничья! {player_roll} = {bot_roll}"
                logger.info(f"🤝 DRAW: bet={bet}, net_win={net_win}")

            return {
                'success': True,
                'player_roll': player_roll,
                'bot_roll': bot_roll,
                'win_amount': net_win,  # Возвращаем ЧИСТЫЙ выигрыш/проигрыш
                'description': description,
                'total_win': bet * 2 if player_roll > bot_roll else 0
            }

        except Exception as e:
            logger.error(f"Ошибка в костях: {e}")
            return {
                'success': False,
                'error': 'Ошибка игры'
            }