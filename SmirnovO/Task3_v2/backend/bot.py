import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import config
from database import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ClickerBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat

        referred_by = None
        if context.args:
            try:
                referred_by = int(context.args[0])
                if referred_by == user.id or not db.get_user(referred_by):
                    referred_by = None
            except ValueError:
                referred_by = None

        user_data = db.get_user(user.id)
        if not user_data:
            user_data = db.create_user(user.id, user.username, chat.id, referred_by)

            if referred_by:
                inviter = db.get_user(referred_by)
                if inviter:
                    inviter.coins += 100
                    inviter.invite_count += 1
                    db.save_user(inviter)

                    user_data.coins += 50
                    db.save_user(user_data)

        keyboard = [
            [InlineKeyboardButton("🎮 Открыть игру", web_app={
                'url': f"{config.Config.WEBAPP_URL}/game/{user.id}"
            })],
            [
                InlineKeyboardButton("📊 Таблица лидеров", callback_data="leaderboard"),
                InlineKeyboardButton("🛍️ Магазин", callback_data="shop")
            ],
            [InlineKeyboardButton("👥 Пригласить друзей", callback_data="invite")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎯 Добро пожаловать в Clicker Game!\n\n"
            "💎 Нажимай на кристалл, зарабатывай очки\n"
            "⚡ Трать энергию и улучшай способности\n"
            "🏆 Соревнуйся с другими игроками\n\n"
            "Открой игру и начни кликать!",
            reply_markup=reply_markup
        )

    async def leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        leaders = db.get_leaderboard(10)

        leaderboard_text = "🏆 Топ-10 игроков:\n\n"
        for player in leaders:
            leaderboard_text += (
                f"{player['rank']}. {player['username'] or 'Аноним'}\n"
                f"   Ур. {player['level']} | {player['score']} очков\n"
            )

        await update.message.reply_text(leaderboard_text)

    async def invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        bot_username = context.bot.username
        invite_link = f"https://t.me/{bot_username}?start={user.id}"

        user_data = db.get_user(user.id)
        invite_count = user_data.invite_count if user_data else 0

        await update.message.reply_text(
            f"👥 Приглашай друзей и получай бонусы!\n\n"
            f"💎 Твоя реферальная ссылка:\n`{invite_link}`\n\n"
            f"🎁 За каждого друга:\n"
            f"• Ты получишь: 100 монет\n"
            f"• Друг получит: 50 монет\n\n"
            f"📊 Приглашено друзей: {invite_count}",
            parse_mode='Markdown'
        )

    async def profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_data = db.get_user(user.id)

        if not user_data:
            await update.message.reply_text("Сначала запусти игру через /start")
            return

        achievements = db.get_achievements(user.id)
        rank = db.get_user_rank(user.id)

        profile_text = (
            f"👤 Профиль {user_data.username or 'Игрока'}\n\n"
            f"🏅 Уровень: {user_data.level}\n"
            f"💎 Очки: {user_data.score}\n"
            f"🪙 Монеты: {user_data.coins}\n"
            f"⚡ Энергия: {user_data.energy}/{user_data.max_energy}\n"
            f"👆 Всего кликов: {user_data.total_clicks}\n"
            f"🏆 Рейтинг: {rank or 'Не в топе'}\n\n"
            f"🎖️ Достижения: {len(achievements)}\n"
        )

        await update.message.reply_text(profile_text)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "leaderboard":
            await self.show_leaderboard(query)
        elif query.data == "invite":
            await self.show_invite(query)
        elif query.data == "shop":
            await self.show_shop(query)

    async def show_leaderboard(self, query):
        leaders = db.get_leaderboard(10)

        leaderboard_text = "🏆 Топ-10 игроков:\n\n"
        for player in leaders:
            leaderboard_text += f"{player['rank']}. {player['username']} - {player['score']} очков\n"

        await query.edit_message_text(leaderboard_text)

    async def show_invite(self, query):
        user = query.from_user
        bot_username = self.application.bot.username
        invite_link = f"https://t.me/{bot_username}?start={user.id}"

        user_data = db.get_user(user.id)
        invite_count = user_data.invite_count if user_data else 0

        await query.edit_message_text(
            f"👥 Пригласи друзей!\n\n"
            f"Ссылка: `{invite_link}`\n\n"
            f"Приглашено: {invite_count} друзей",
            parse_mode='Markdown'
        )

    async def show_shop(self, query):
        shop_text = (
            "🛍️ Магазин улучшений:\n\n"
            "💎 Двойной клик (+2 за тап) - 100 монет\n"
            "🤖 Автокликер (+1 в сек) - 500 монет\n"
            "🔋 Больше энергии (200 макс) - 300 монет\n"
            "⚡ Быстрое восстановление (2/мин) - 400 монет\n\n"
            "Открой игру чтобы купить улучшения!"
        )

        await query.edit_message_text(shop_text)

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("leaderboard", self.leaderboard))
        self.application.add_handler(CommandHandler("invite", self.invite))
        self.application.add_handler(CommandHandler("profile", self.profile))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))

    async def run(self):
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        await self.application.run_polling()