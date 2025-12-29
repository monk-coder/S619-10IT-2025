"""
Обработчики основных команд бота
Команды старта, баланса, топа игроков и бонусов
"""
import time
import random
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import Database
from keyboards import get_main_keyboard, get_back_keyboard
from config import EMOJI, STARTING_BALANCE, REFERRAL_BONUS, BONUS_AMOUNT, BONUS_COOLDOWN

logger = logging.getLogger(__name__)
db = Database()

MEDALS_EMOJI = {1: "🥇", 2: "🥈", 3: "🥉"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start с реферальной системой"""
    user = update.effective_user
    referred_by = _get_referred_by(context.args)
    
    user_data = db.get_user(user.id)
    
    if not user_data:
        # Создаем пользователя (referral_code теперь НЕ используется)
        db.create_user(user.id, user.username, referred_by)
        await _send_welcome_message(update, user, referred_by)
    else:
        await update.message.reply_text(f"С возвращением, {user.first_name}! 🎰",
                                      reply_markup=get_main_keyboard())

def _get_referred_by(args: list) -> int | None:
    """Извлечь ID реферера из аргументов с проверкой"""
    if not args:
        return None
    
    try:
        referred_id = int(args[0])
        # Проверяем, что число положительное
        return referred_id if referred_id > 0 else None
    except (ValueError, TypeError):
        logger.warning(f"Некорректный referral ID: {args[0]}")
        return None

async def _send_welcome_message(update: Update, user, referred_by: int):
    """Отправить приветственное сообщение"""
    welcome_text = _build_welcome_text(user.first_name, referred_by)
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

def _build_welcome_text(user_name: str, referred_by: int) -> str:
    """Сформировать текст приветствия"""
    base_text = (
        f"🎉 Добро пожаловать в казино-бот, {user_name}!\n\n"
        f"💰 Стартовый баланс: {STARTING_BALANCE} монет\n"
        f"🎰 Доступные игры: Слоты, Кости, Блекджек, Рулетка\n"
        f"🎁 Бонус {BONUS_AMOUNT} монет каждые 3 часа\n\n"
        f"📝 Используйте кнопки меню для навигации"
    )

    if referred_by:
        base_text += f"\n\n🎁 Вы пришли по реферальной ссылке! Бонус начислен пригласившему."

    return base_text

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать баланс и статистику пользователя - БЕЗ referral_code"""
    user = update.effective_user
    user_data = db.get_user(user.id)

    if user_data:
        balance_text = (
            f"{EMOJI['money']} **Баланс:** {user_data['balance']} монет\n"
            f"🎮 **Сыграно игр:** {user_data['games_played']}\n\n"
            f"*Приглашайте друзей и получайте {REFERRAL_BONUS} монет за каждого!*"
        )
        await update.message.reply_text(balance_text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Пользователь не найден. Используйте /start")

async def show_top_players(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать топ-10 игроков по балансу"""
    top_players = db.get_top_players(10)

    if not top_players:
        await update.message.reply_text("📊 Пока нет данных о игроках.")
        return

    top_text = f"{EMOJI['trophy']} **ТОП-10 ИГРОКОВ**\n\n"

    for i, player in enumerate(top_players, 1):
        medal = MEDALS_EMOJI.get(i, f"{i}.")
        username = player['username'] or 'Аноним'
        top_text += f"{medal} {username} - {player['balance']} монет\n"

    await update.message.reply_text(top_text, reply_markup=get_back_keyboard())

async def get_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выдать бонус раз в 3 часа"""
    user = update.effective_user
    user_data = db.get_user(user.id)

    if not user_data:
        await update.message.reply_text("❌ Сначала используйте /start")
        return

    last_bonus = db.get_last_bonus_time(user.id)
    current_time = time.time()

    if current_time - last_bonus < BONUS_COOLDOWN:
        remaining_time = BONUS_COOLDOWN - (current_time - last_bonus)
        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)

        await update.message.reply_text(
            f"⏰ Бонус можно получить через {hours}ч {minutes}м\n"
            f"🎁 Следующий бонус: {BONUS_AMOUNT} монет"
        )
    else:
        db.give_bonus(user_id=user.id, amount=BONUS_AMOUNT)
        db.update_bonus_time(user.id)
        user_data = db.get_user(user.id)

        await update.message.reply_text(
            f"🎉 Вы получили бонус: {BONUS_AMOUNT} монет!\n"
            f"💰 Ваш баланс: {user_data['balance']} монет\n\n"
            f"⏰ Следующий бонус через 3 часа"
        )
