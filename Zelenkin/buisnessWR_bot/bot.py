import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

from config import BOT_TOKEN, CATEGORIES, INCOME_CATEGORIES
from database import Database
from keyboards import (
    get_categories_keyboard, get_income_categories_keyboard,
    get_delete_keyboard, get_main_menu_keyboard, get_stats_keyboard
)
from utils import format_statistics, format_history, parse_amount, format_amount

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
SELECTING_CATEGORY, ENTERING_AMOUNT, ENTERING_COMMENT = range(3)
SELECTING_INCOME_SOURCE, ENTERING_INCOME_AMOUNT, ENTERING_INCOME_COMMENT = range(3, 6)


class FinanceBot:
    def __init__(self):
        self.db = Database('finance_bot.db')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name)

        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            "Я помогу тебе вести учёт финансов.\n\n"
            "<b>Основные команды:</b>\n"
            "💸 /add - Добавить расход\n"
            "💰 /income - Добавить доход\n"
            "📊 /today - Статистика за сегодня\n"
            "📆 /week - Статистика за неделю\n"
            "📈 /month - Статистика за месяц\n"
            "📝 /history - История операций\n"
            "🎯 /set_budget - Установить бюджет\n"
            "🎯 /goals - Прогресс по бюджетам\n\n"
            "Или используй кнопки ниже:"
        )

        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "📱 <b>Главное меню</b>\n\nВыберите действие:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )

    async def start_add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления расхода"""
        user_id = update.effective_user.id

        # Очищаем предыдущее состояние
        context.user_data.clear()

        if update.message:
            await update.message.reply_text(
                "💸 <b>Добавление расхода</b>\n\nВыберите категорию:",
                reply_markup=get_categories_keyboard(),
                parse_mode='HTML'
            )
        else:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "💸 <b>Добавление расхода</b>\n\nВыберите категорию:",
                reply_markup=get_categories_keyboard(),
                parse_mode='HTML'
            )

        return SELECTING_CATEGORY

    async def category_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора категории"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        category_key = query.data.replace('category_', '')
        category_name = CATEGORIES.get(category_key, category_key)

        # Сохраняем выбранную категорию в context.user_data
        context.user_data['category'] = category_key
        context.user_data['category_name'] = category_name

        await query.edit_message_text(
            f"📝 Категория: <b>{category_name}</b>\n\n"
            "Введите сумму расхода:\n"
            "<i>Например: 500 или 150.50</i>",
            parse_mode='HTML'
        )

        return ENTERING_AMOUNT

    async def amount_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка введенной суммы"""
        user_id = update.effective_user.id
        amount_text = update.message.text

        try:
            amount = parse_amount(amount_text)
            if amount <= 0:
                await update.message.reply_text("❌ Сумма должна быть больше нуля")
                return ENTERING_AMOUNT
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return ENTERING_AMOUNT

        # Сохраняем сумму в context.user_data
        context.user_data['amount'] = amount

        await update.message.reply_text(
            "💬 Введите комментарий (или отправьте '-' чтобы пропустить):",
            reply_markup=ReplyKeyboardRemove()
        )

        return ENTERING_COMMENT

    async def comment_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка комментария и сохранение транзакции"""
        user_id = update.effective_user.id
        comment = update.message.text

        if comment == '-':
            comment = None

        # Получаем сохраненные данные из context.user_data
        category = context.user_data.get('category')
        amount = context.user_data.get('amount')
        category_name = context.user_data.get('category_name')

        if not category or not amount:
            await update.message.reply_text("❌ Ошибка: данные не найдены. Начните заново.")
            context.user_data.clear()
            return ConversationHandler.END

        # Сохраняем в базу
        expense_id = self.db.add_expense(user_id, amount, category, comment)

        # Очищаем состояние
        context.user_data.clear()

        # Формируем сообщение
        message = (
            f"✅ <b>Расход добавлен!</b>\n\n"
            f"💵 Сумма: {format_amount(amount)}\n"
            f"📂 Категория: {category_name}\n"
        )
        if comment:
            message += f"💬 Комментарий: {comment}\n"

        message += f"\n📊 Используйте /today для просмотра статистики"

        await update.message.reply_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )

        # Проверяем бюджет
        await self._check_budget_notification(user_id, category, amount, context)

        return ConversationHandler.END

    async def _check_budget_notification(self, user_id: int, category: str, amount: float,
                                         context: ContextTypes.DEFAULT_TYPE):
        """Проверка уведомлений о бюджете"""
        try:
            budget_info = self.db.get_category_spending_vs_budget(user_id, category)

            if budget_info['budget'] > 0:
                percentage = budget_info['percentage']
                category_name = CATEGORIES.get(category, category)

                if percentage >= 100:
                    message = (
                        f"🚨 <b>Превышен бюджет!</b>\n\n"
                        f"📂 Категория: {category_name}\n"
                        f"💸 Потрачено: {format_amount(budget_info['spent'])}\n"
                        f"🎯 Бюджет: {format_amount(budget_info['budget'])}\n"
                        f"📊 Превышение: {format_amount(budget_info['spent'] - budget_info['budget'])}"
                    )
                elif percentage >= 80:
                    message = (
                        f"⚠️ <b>Приближение к лимиту</b>\n\n"
                        f"📂 Категория: {category_name}\n"
                        f"💸 Потрачено: {format_amount(budget_info['spent'])}\n"
                        f"🎯 Бюджет: {format_amount(budget_info['budget'])}\n"
                        f"📊 Использовано: {percentage:.1f}%"
                    )
                else:
                    return

                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Ошибка при проверке бюджета: {e}")

    async def start_add_income(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления дохода"""
        # Очищаем предыдущее состояние
        context.user_data.clear()

        if update.message:
            await update.message.reply_text(
                "💰 <b>Добавление дохода</b>\n\nВыберите источник:",
                reply_markup=get_income_categories_keyboard(),
                parse_mode='HTML'
            )
        else:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "💰 <b>Добавление дохода</b>\n\nВыберите источник:",
                reply_markup=get_income_categories_keyboard(),
                parse_mode='HTML'
            )

        return SELECTING_INCOME_SOURCE

    async def income_source_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора источника дохода"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        source_key = query.data.replace('income_', '')
        source_name = INCOME_CATEGORIES.get(source_key, source_key)

        # Сохраняем выбранный источник в context.user_data
        context.user_data['income_source'] = source_key
        context.user_data['income_source_name'] = source_name

        await query.edit_message_text(
            f"📝 Источник: <b>{source_name}</b>\n\n"
            "Введите сумму дохода:\n"
            "<i>Например: 5000 или 1500.50</i>",
            parse_mode='HTML'
        )

        return ENTERING_INCOME_AMOUNT

    async def income_amount_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка введенной суммы дохода"""
        user_id = update.effective_user.id
        amount_text = update.message.text

        try:
            amount = parse_amount(amount_text)
            if amount <= 0:
                await update.message.reply_text("❌ Сумма должна быть больше нуля")
                return ENTERING_INCOME_AMOUNT
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return ENTERING_INCOME_AMOUNT

        # Сохраняем сумму в context.user_data
        context.user_data['income_amount'] = amount

        await update.message.reply_text(
            "💬 Введите комментарий (или отправьте '-' чтобы пропустить):",
            reply_markup=ReplyKeyboardRemove()
        )

        return ENTERING_INCOME_COMMENT

    async def income_comment_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка комментария и сохранение дохода"""
        user_id = update.effective_user.id
        comment = update.message.text

        if comment == '-':
            comment = None

        # Получаем сохраненные данные из context.user_data
        source = context.user_data.get('income_source')
        amount = context.user_data.get('income_amount')
        source_name = context.user_data.get('income_source_name')

        if not source or not amount:
            await update.message.reply_text("❌ Ошибка: данные не найдены. Начните заново.")
            context.user_data.clear()
            return ConversationHandler.END

        # Сохраняем в базу
        income_id = self.db.add_income(user_id, amount, source, comment)

        # Очищаем состояние
        context.user_data.clear()

        # Формируем сообщение
        message = (
            f"✅ <b>Доход добавлен!</b>\n\n"
            f"💵 Сумма: {format_amount(amount)}\n"
            f"📂 Источник: {source_name}\n"
        )
        if comment:
            message += f"💬 Комментарий: {comment}\n"

        await update.message.reply_text(
            message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )

        return ConversationHandler.END

    async def show_stats_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню статистики"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "📊 <b>Статистика</b>\n\nВыберите период:",
            reply_markup=get_stats_keyboard(),
            parse_mode='HTML'
        )

    async def show_today_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику за сегодня"""
        user_id = update.effective_user.id

        if update.message:
            expenses = self.db.get_today_expenses(user_id)
            text = format_statistics(expenses, "сегодня")
            await update.message.reply_text(
                text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            query = update.callback_query
            await query.answer()
            expenses = self.db.get_today_expenses(user_id)
            text = format_statistics(expenses, "сегодня")
            await query.edit_message_text(
                text,
                reply_markup=get_stats_keyboard(),
                parse_mode='HTML'
            )

    async def show_week_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику за неделю"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        expenses = self.db.get_week_expenses(user_id)
        text = format_statistics(expenses, "неделю")

        await query.edit_message_text(
            text,
            reply_markup=get_stats_keyboard(),
            parse_mode='HTML'
        )

    async def show_month_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику за месяц"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        expenses = self.db.get_month_expenses(user_id)
        text = format_statistics(expenses, "месяц")

        await query.edit_message_text(
            text,
            reply_markup=get_stats_keyboard(),
            parse_mode='HTML'
        )

    async def show_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать историю транзакций"""
        user_id = update.effective_user.id

        expenses = self.db.get_recent_expenses(user_id, 10)
        text = format_history(expenses)

        if update.message:
            await update.message.reply_text(
                text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='HTML'
            )

    async def delete_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удаление транзакции"""
        query = update.callback_query
        await query.answer()

        if query.data.startswith('delete_'):
            expense_id = int(query.data.replace('delete_', ''))
            user_id = query.from_user.id

            if self.db.delete_expense(expense_id, user_id):
                await query.edit_message_text(
                    "✅ Транзакция удалена",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await query.edit_message_text(
                    "❌ Ошибка удаления",
                    reply_markup=get_main_menu_keyboard()
                )
        elif query.data == 'cancel_delete':
            await query.edit_message_text(
                "❌ Удаление отменено",
                reply_markup=get_main_menu_keyboard()
            )

    async def set_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установка бюджета"""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Использование: /set_budget <категория> <сумма>\n\n"
                "Пример: /set_budget еда 5000\n"
                "Доступные категории: " + ", ".join(CATEGORIES.keys())
            )
            return

        category_key = context.args[0].lower()
        amount_text = context.args[1]

        # Проверяем категорию
        if category_key not in CATEGORIES:
            await update.message.reply_text(
                f"❌ Неверная категория. Доступные: {', '.join(CATEGORIES.keys())}"
            )
            return

        # Парсим сумму
        try:
            amount = parse_amount(amount_text)
            if amount <= 0:
                await update.message.reply_text("❌ Сумма должна быть больше нуля")
                return
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return

        # Сохраняем бюджет
        user_id = update.effective_user.id
        self.db.set_budget(user_id, category_key, amount)
        category_name = CATEGORIES[category_key]

        await update.message.reply_text(
            f"✅ Бюджет установлен!\n\n"
            f"📂 Категория: {category_name}\n"
            f"🎯 Лимит: {format_amount(amount)}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )

    async def show_goals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать прогресс по бюджетам"""
        user_id = update.effective_user.id
        budgets = self.db.get_budgets(user_id)

        if not budgets:
            message_text = (
                "🎯 Бюджеты не установлены\n\n"
                "Используйте /set_budget для установки лимитов\n"
                "Пример: /set_budget еда 5000"
            )
        else:
            result = ["🎯 <b>Прогресс по бюджетам:</b>\n"]

            for budget in budgets:
                category = budget['category']
                budget_amount = budget['amount']
                category_name = CATEGORIES.get(category, category)

                spending_info = self.db.get_category_spending_vs_budget(user_id, category)

                percentage = spending_info['percentage']
                status_icon = "🟢" if percentage < 80 else "🟡" if percentage < 100 else "🔴"

                if percentage >= 100:
                    remaining_text = f"📊 Превышение: {format_amount(abs(spending_info['remaining']))}"
                else:
                    remaining_text = f"📊 {percentage:.1f}% | Осталось: {format_amount(spending_info['remaining'])}"

                result.append(
                    f"{status_icon} <b>{category_name}</b>\n"
                    f"   💸 Потрачено: {format_amount(spending_info['spent'])} / {format_amount(budget_amount)}\n"
                    f"   {remaining_text}\n"
                )

            message_text = "\n".join(result)

        # Проверяем, откуда пришел запрос - из сообщения или callback
        if update.message:
            await update.message.reply_text(
                message_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                message_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode='HTML'
            )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена текущей операции через команду /cancel"""
        context.user_data.clear()

        await update.message.reply_text(
            "❌ Операция отменена",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

    async def cancel_conv(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена из ConversationHandler через inline-кнопку"""
        query = update.callback_query
        await query.answer()

        context.user_data.clear()

        await query.edit_message_text(
            "❌ Операция отменена",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

    async def fallback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик для любых текстовых сообщений вне диалогов"""
        await update.message.reply_text(
            "🤔 Не понимаю команду. Используйте /start для начала работы.",
            reply_markup=get_main_menu_keyboard()
        )

    def setup_handlers(self, application: Application):
        """Настройка обработчиков"""

        # Conversation Handler для расходов
        expense_conv = ConversationHandler(
            entry_points=[
                CommandHandler('add', self.start_add_expense),
                CallbackQueryHandler(self.start_add_expense, pattern='^add_expense$')
            ],
            states={
                SELECTING_CATEGORY: [
                    CallbackQueryHandler(self.category_selected, pattern='^category_'),
                    CallbackQueryHandler(self.cancel_conv, pattern='^cancel$')
                ],
                ENTERING_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.amount_received)
                ],
                ENTERING_COMMENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.comment_received)
                ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
            per_message=False
        )

        # Conversation Handler для доходов
        income_conv = ConversationHandler(
            entry_points=[
                CommandHandler('income', self.start_add_income),
                CallbackQueryHandler(self.start_add_income, pattern='^add_income$')
            ],
            states={
                SELECTING_INCOME_SOURCE: [
                    CallbackQueryHandler(self.income_source_selected, pattern='^income_'),
                    CallbackQueryHandler(self.cancel_conv, pattern='^cancel$')
                ],
                ENTERING_INCOME_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.income_amount_received)
                ],
                ENTERING_INCOME_COMMENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.income_comment_received)
                ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
            per_message=False
        )

        # Добавляем обработчики
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(expense_conv)
        application.add_handler(income_conv)
        application.add_handler(CommandHandler('today', self.show_today_stats))
        application.add_handler(CommandHandler('week', self.show_week_stats))
        application.add_handler(CommandHandler('month', self.show_month_stats))
        application.add_handler(CommandHandler('history', self.show_history))
        application.add_handler(CommandHandler('set_budget', self.set_budget))
        application.add_handler(CommandHandler('goals', self.show_goals))

        # Обработчики callback-запросов
        application.add_handler(CallbackQueryHandler(self.show_main_menu, pattern='^main_menu$'))
        application.add_handler(CallbackQueryHandler(self.show_stats_menu, pattern='^stats$'))
        application.add_handler(CallbackQueryHandler(self.show_today_stats, pattern='^stats_today$'))
        application.add_handler(CallbackQueryHandler(self.show_week_stats, pattern='^stats_week$'))
        application.add_handler(CallbackQueryHandler(self.show_month_stats, pattern='^stats_month$'))
        application.add_handler(CallbackQueryHandler(self.show_history, pattern='^history$'))
        application.add_handler(CallbackQueryHandler(self.show_goals, pattern='^budgets$'))
        application.add_handler(CallbackQueryHandler(self.delete_expense, pattern='^(delete_|cancel_delete)'))

        # Обработчик для любых текстовых сообщений (fallback)
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.fallback_handler
        ))


def main():
    """Основная функция"""
    bot = FinanceBot()

    application = Application.builder().token(BOT_TOKEN).build()
    bot.setup_handlers(application)

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()