import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import sys
import os
from datetime import datetime

# Добавляем корневую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from .database import Database
from .utils import generate_game_code, validate_date, format_participant_info, shuffle_participants

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
PROFILE, BIO = range(2)
GAME_NAME, GAME_DATE, GAME_MIN_PARTICIPANTS = range(2, 5)
MESSAGE_GAME_SELECT, MESSAGE_TEXT = range(5, 7)


class SecretSantaBot:
    def __init__(self):
        self.db = Database(Config.DB_NAME)
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        self.setup_handlers()

    async def start(self, update, context):
        """Обработчик команды /start"""
        try:
            user = update.effective_user

            # Пытаемся добавить пользователя в базу
            success = self.db.add_user(user.id, user.username, user.full_name)

            if not success:
                await update.message.reply_text(
                    "❌ Произошла ошибка при регистрации. Попробуйте позже."
                )
                return

            # Проверяем непрочитанные сообщения
            unread_count = self.db.get_unread_messages_count(user.id)
            messages_notification = ""
            if unread_count > 0:
                messages_notification = f"\n📨 У вас {unread_count} непрочитанных сообщений! Используйте /messages"

            welcome_text = f"""
🎅 Добро пожаловать в Тайного Санту, {user.full_name}!

Я помогу организовать обмен подарками!

Основные команды:
/start - Начало работы
/profile - Настроить профиль (ФИО и информация о себе)
/create_game - Создать новую игру
/join - Присоединиться к игре по коду
/leave - Выйти из игры
/status - Посмотреть мои игры
/participants - Посмотреть участников игры
/my_recipient - Посмотреть моего получателя подарка
/mix - Запустить жеребьёвку (для организатора)
/message - Отправить анонимное сообщение
/messages - Проверить новые сообщения
/help - Помощь{messages_notification}

🚀 Начните с настройки профиля командой /profile!
            """
            await update.message.reply_text(welcome_text)
            logger.info(f"✅ Новый пользователь: {user.full_name} ({user.id})")

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /start: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
            )

    async def help_command(self, update, context):
        """Обработчик команды /help"""
        help_text = """
🎄 Тайный Санта Бот - помощь

👤 ЛИЧНЫЙ КАБИНЕТ:
/start - Регистрация и начало
/profile - Настройка профиля (ФИО, биография)

🎮 УПРАВЛЕНИЕ ИГРАМИ:
/create_game - Создать новую игру
/join [код] - Присоединиться к игре
/leave - Выйти из игры (до жеребьёвки)
/status - Просмотр моих игр
/participants - Участники игры

🎁 ЖЕРЕБЬЁВКА И ПОЛУЧАТЕЛИ:
/mix - Запустить жеребьёвку (только организатор)
/my_recipient - Посмотреть моего получателя подарка

📨 АНОНИМНЫЕ СООБЩЕНИЙ:
/message - Отправить анонимное сообщение получателю
/messages - Проверить новые сообщения

❓ ДОПОЛНИТЕЛЬНО:
/help - Эта справка

📌 Примеры:
/join ABC123
/create_game
/my_recipient ABC123
/mix ABC123
/message
/messages 
        """
        await update.message.reply_text(help_text)

    # === ОБРАБОТЧИКИ ПРОФИЛЯ ===

    async def profile(self, update, context):
        """Начало настройки профиля"""
        try:
            user = update.effective_user

            # Проверяем текущий профиль
            user_data = self.db.get_user(user.id)
            if user_data and user_data[2]:  # Если уже есть ФИО
                current_profile = f"""
📋 Ваш текущий профиль:
👤 ФИО: {user_data[2] or 'Не указано'}
📝 О себе: {user_data[3] or 'Не указано'}

Хотите изменить профиль?
                """
                await update.message.reply_text(current_profile)

            await update.message.reply_text(
                "👤 Давайте настроим ваш профиль!\n\n"
                "Введите ваше ФИО (как к вам обращаться):\n\n"
                "❌ Для отмены отправьте /cancel"
            )
            return PROFILE

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /profile: {e}")
            await update.message.reply_text("❌ Ошибка при настройке профиля.")
            return ConversationHandler.END

    async def set_profile(self, update, context):
        """Сохранение ФИО пользователя"""
        try:
            full_name = update.message.text

            # Сохраняем в контексте для следующего шага
            context.user_data['full_name'] = full_name

            await update.message.reply_text(
                "📝 Отлично! Теперь расскажите о себе:\n"
                "- Ваши хобби\n"
                "- Интересы\n"
                "- Что вас радует\n\n"
                "Эта информация поможет вашему Тайному Санте выбрать лучший подарок!\n\n"
                "❌ Для отмены отправьте /cancel"
            )
            return BIO

        except Exception as e:
            logger.error(f"❌ Ошибка в set_profile: {e}")
            await update.message.reply_text("❌ Ошибка при сохранении профиля.")
            return ConversationHandler.END

    async def set_bio(self, update, context):
        """Сохранение биографии пользователя"""
        try:
            user_id = update.effective_user.id
            full_name = context.user_data['full_name']
            bio = update.message.text

            # Сохраняем в базу данных
            success = self.db.update_user_profile(user_id, full_name, bio)

            if not success:
                await update.message.reply_text("❌ Ошибка при сохранении профиля.")
                return ConversationHandler.END

            # Формируем подтверждение
            profile_text = f"""
✅ Профиль успешно обновлен!

👤 {full_name}
📝 О себе:
{bio}

Теперь вы можете:
- Создать игру командой /create_game
- Или присоединиться к существующей игре
            """

            await update.message.reply_text(profile_text)

            # Очищаем временные данные
            context.user_data.clear()

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"❌ Ошибка в set_bio: {e}")
            await update.message.reply_text("❌ Ошибка при сохранении профиля.")
            return ConversationHandler.END

    # === ОБРАБОТЧИКИ СОЗДАНИЯ ИГР ===

    async def create_game(self, update, context):
        """Начало создания игры"""
        try:
            await update.message.reply_text(
                "🎮 Создание новой игры Тайного Санты!\n\n"
                "Введите название для вашей игры:\n\n"
                "❌ Для отмены отправьте /cancel"
            )
            return GAME_NAME

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /create_game: {e}")
            await update.message.reply_text("❌ Ошибка при создании игры.")
            return ConversationHandler.END

    async def set_game_name(self, update, context):
        """Сохранение названия игры"""
        try:
            game_name = update.message.text
            context.user_data['game_name'] = game_name

            await update.message.reply_text(
                "📅 Теперь введите дату жеребьёвки:\n"
                "Формат: ДД.ММ.ГГГГ\n\n"
                "Пример: 25.12.2024\n\n"
                "❌ Для отмены отправьте /cancel"
            )
            return GAME_DATE

        except Exception as e:
            logger.error(f"❌ Ошибка в set_game_name: {e}")
            await update.message.reply_text("❌ Ошибка при создании игры.")
            return ConversationHandler.END

    async def set_game_date(self, update, context):
        """Сохранение даты игры"""
        try:
            date_text = update.message.text

            if not validate_date(date_text):
                await update.message.reply_text(
                    "❌ Неверный формат даты!\n"
                    "Используйте формат: ДД.ММ.ГГГГ\n"
                    "Пример: 25.12.2024\n\n"
                    "Попробуйте снова:"
                )
                return GAME_DATE

            context.user_data['game_date'] = date_text

            await update.message.reply_text(
                "👥 Введите минимальное количество участников:\n"
                "Минимум: 3 человека\n\n"
                "❌ Для отмены отправьте /cancel"
            )
            return GAME_MIN_PARTICIPANTS

        except Exception as e:
            logger.error(f"❌ Ошибка в set_game_date: {e}")
            await update.message.reply_text("❌ Ошибка при создании игры.")
            return ConversationHandler.END

    async def set_min_participants(self, update, context):
        """Сохранение минимального количества участников и создание игры"""
        try:
            min_participants = int(update.message.text)

            if min_participants < 3:
                await update.message.reply_text(
                    "❌ Минимальное количество участников - 3!\n"
                    "Пожалуйста, введите число от 3 и больше:"
                )
                return GAME_MIN_PARTICIPANTS

            # Создаем игру
            game_code = generate_game_code()
            organizer_id = update.effective_user.id
            game_name = context.user_data['game_name']
            game_date = context.user_data['game_date']

            success = self.db.create_game(game_code, game_name, organizer_id, game_date, min_participants)

            if not success:
                await update.message.reply_text("❌ Ошибка при создании игры.")
                return ConversationHandler.END

            # Добавляем организатора в участники
            self.db.join_game(game_code, organizer_id)

            # Формируем сообщение об успехе
            success_message = f"""
🎉 Игра создана успешно!

📛 Название: {game_name}
🆔 Код игры: `{game_code}`
📅 Дата жеребьёвки: {game_date}
👥 Минимум участников: {min_participants}

📣 Отправьте код игры друзьям:
`{game_code}`

👥 Участники могут присоединиться командой:
/join {game_code}

🎁 Для запуска жеребьёвки используйте:
/mix {game_code}

💡 Используйте /status чтобы посмотреть список участников
            """

            await update.message.reply_text(success_message)

            # Очищаем временные данные
            context.user_data.clear()

            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text(
                "❌ Пожалуйста, введите число:\n"
                "Пример: 5"
            )
            return GAME_MIN_PARTICIPANTS
        except Exception as e:
            logger.error(f"❌ Ошибка в set_min_participants: {e}")
            await update.message.reply_text("❌ Ошибка при создании игры.")
            return ConversationHandler.END

    # === КОМАНДА JOIN ===

    async def join_game(self, update, context):
        """Присоединение к игре"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ Используйте: /join КОД_ИГРЫ\n\n"
                    "Пример: /join ABC123"
                )
                return

            game_code = context.args[0].upper()
            user_id = update.effective_user.id

            # Проверяем, существует ли игра
            user_games = self.db.get_user_active_games(user_id)
            existing_game = any(game[0] == game_code for game in user_games)

            if existing_game:
                await update.message.reply_text("❌ Вы уже участвуете в этой игре!")
                return

            success = self.db.join_game(game_code, user_id)

            if success:
                await update.message.reply_text(
                    f"✅ Вы успешно присоединились к игре {game_code}!\n\n"
                    "Не забудьте:\n"
                    "• Заполнить профиль командой /profile\n"
                    "• Следить за уведомлениями от организатора\n\n"
                    "❌ Чтобы выйти из игры, используйте /leave"
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка присоединения.\n"
                    "Проверьте код игры или попробуйте позже."
                )

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /join: {e}")
            await update.message.reply_text("❌ Ошибка при присоединении к игре.")

    # === КОМАНДА LEAVE ===

    async def leave_game(self, update, context):
        """Выход из игры"""
        try:
            user_id = update.effective_user.id

            # Получаем активные игры пользователя
            user_games = self.db.get_user_active_games(user_id)

            if not user_games:
                await update.message.reply_text(
                    "🤷 Вы не участвуете ни в одной активной игре.\n\n"
                    "Присоединитесь к игре командой:\n"
                    "/join КОД_ИГРЫ"
                )
                return

            # Если указан код игры в аргументах
            if context.args:
                game_code = context.args[0].upper()

                # Проверяем, участвует ли пользователь в указанной игре
                user_game_codes = [game[0] for game in user_games]
                if game_code not in user_game_codes:
                    await update.message.reply_text(
                        f"❌ Вы не участвуете в игре {game_code}.\n\n"
                        "Ваши игры:\n" +
                        "\n".join([f"• {game[0]} - {game[1]}" for game in user_games])
                    )
                    return

                # Выходим из указанной игры
                result = self.db.leave_game(game_code, user_id)

                if result == "organizer":
                    await update.message.reply_text(
                        f"❌ Вы организатор игры {game_code}!\n"
                        "Организатор не может выйти из игры.\n\n"
                        "Если хотите удалить игру, свяжитесь с администратором."
                    )
                elif result == "success":
                    # Проверяем, была ли жеребьёвка
                    if self.db.is_game_drawn(game_code):
                        await update.message.reply_text(
                            f"⚠️ Вы вышли из игры {game_code}, но жеребьёвка уже проведена.\n"
                            "Пожалуйста, предупредите организатора."
                        )
                    else:
                        await update.message.reply_text(
                            f"✅ Вы успешно вышли из игры {game_code}.\n\n"
                            "Можете присоединиться к другой игре командой /join"
                        )
                else:
                    await update.message.reply_text(
                        "❌ Ошибка при выходе из игры.\n"
                        "Попробуйте позже или свяжитесь с организатором."
                    )

                return

            # Если игр несколько - показываем список для выбора
            if len(user_games) > 1:
                games_list = "\n".join([
                    f"• `{game[0]}` - {game[1]} ({game[3]} участников)"
                    for game in user_games
                ])

                await update.message.reply_text(
                    f"🎮 Вы участвуете в нескольких играх:\n\n{games_list}\n\n"
                    "Для выхода из конкретной игры используйте:\n"
                    "/leave КОД_ИГРЫ\n\n"
                    "Пример: /leave ABC123"
                )
                return

            # Если игра одна - выходим из нее
            game_code, game_name, _, participant_count, organizer_id, is_drawn = user_games[0]

            # Проверяем, является ли пользователь организатором
            if organizer_id == user_id:
                await update.message.reply_text(
                    f"❌ Вы организатор игры {game_code}!\n"
                    "Организатор не может выйти из игры.\n\n"
                    "Если хотите удалить игру, свяжитесь с администратором."
                )
                return

            # Выходим из игры
            result = self.db.leave_game(game_code, user_id)

            if result == "success":
                if is_drawn:
                    await update.message.reply_text(
                        f"⚠️ Вы вышли из игры {game_code}, но жеребьёвка уже проведена.\n"
                        "Пожалуйста, предупредите организатора игры."
                    )
                else:
                    await update.message.reply_text(
                        f"✅ Вы успешно вышли из игры {game_code}.\n\n"
                        "Можете присоединиться к другой игре командой /join"
                    )
            else:
                await update.message.reply_text(
                    "❌ Ошибка при выходе из игры.\n"
                    "Попробуйте позже или свяжитесь с организатором."
                )

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /leave: {e}")
            await update.message.reply_text("❌ Ошибка при выходе из игры.")

    # === КОМАНДА STATUS ===

    async def game_status(self, update, context):
        """Статус игр пользователя"""
        try:
            user_id = update.effective_user.id
            user_games = self.db.get_user_active_games(user_id)

            if not user_games:
                await update.message.reply_text(
                    "🤷 Вы пока не участвуете ни в одной игре.\n\n"
                    "Создайте свою игру командой /create_game\n"
                    "Или присоединитесь к существующей командой /join КОД"
                )
                return

            status_text = "🎮 Ваши активные игры:\n\n"

            for game in user_games:
                game_code, game_name, draw_date, participant_count, organizer_id, is_drawn = game

                status_text += f"🆔 Код: `{game_code}`\n"
                status_text += f"📛 Название: {game_name}\n"
                status_text += f"📅 Жеребьёвка: {draw_date}\n"
                status_text += f"👥 Участников: {participant_count}\n"

                if organizer_id == user_id:
                    status_text += "🎯 Вы организатор\n"
                    if not is_drawn:
                        status_text += f"🎁 Запустить жеребьёвку: /mix {game_code}\n"
                else:
                    status_text += "🎅 Вы участник\n"

                if is_drawn:
                    status_text += "✅ Жеребьёвка проведена\n"
                    # Добавляем информацию о возможности посмотреть получателя
                    status_text += f"👀 Мой получатель: /my_recipient {game_code}\n"

                    # Показываем количество непрочитанных сообщений для этой игры
                    unread_count = self.db.get_unread_messages_count(user_id, game_code)
                    if unread_count > 0:
                        status_text += f"📨 Непрочитанных сообщений: {unread_count}\n"
                    status_text += f"✉️ Отправить сообщение: /message\n"
                else:
                    status_text += "⏳ Жеребьёвка ожидается\n"

                status_text += f"👀 Участники: /participants {game_code}\n"
                status_text += f"❌ Выйти: /leave {game_code}\n\n"

            await update.message.reply_text(status_text)

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /status: {e}")
            await update.message.reply_text("❌ Ошибка при получении статуса игр.")

    # === КОМАНДА PARTICIPANTS ===

    async def show_participants(self, update, context):
        """Показать участников игры"""
        try:
            user_id = update.effective_user.id

            # Если указан код игры в аргументах
            if context.args:
                game_code = context.args[0].upper()

                # Проверяем, участвует ли пользователь в игре
                if not self.db.is_user_in_game(user_id, game_code):
                    await update.message.reply_text(
                        f"❌ Вы не участвуете в игре {game_code}.\n\n"
                        "Присоединитесь к игре командой:\n"
                        f"/join {game_code}"
                    )
                    return
            else:
                # Если код не указан, ищем игры пользователя
                user_games = self.db.get_user_active_games(user_id)

                if not user_games:
                    await update.message.reply_text(
                        "🤷 Вы не участвуете ни в одной игре.\n\n"
                        "Присоединитесь к игре командой:\n"
                        "/join КОД_ИГРЫ"
                    )
                    return

                if len(user_games) > 1:
                    games_list = "\n".join([
                        f"• `{game[0]}` - {game[1]} ({game[3]} участников)"
                        for game in user_games
                    ])

                    await update.message.reply_text(
                        f"🎮 Вы участвуете в нескольких играх:\n\n{games_list}\n\n"
                        "Для просмотра участников конкретной игры используйте:\n"
                        "/participants КОД_ИГРЫ\n\n"
                        "Пример: /participants ABC123"
                    )
                    return

                # Если игра одна - используем ее код
                game_code = user_games[0][0]

            # Получаем информацию об игре
            game_info = self.db.get_game_info(game_code)
            if not game_info:
                await update.message.reply_text("❌ Игра не найдена.")
                return

            game_name, organizer_id, draw_date, min_participants, current_participants = game_info

            # Получаем участников
            participants = self.db.get_game_participants_details(game_code)

            if not participants:
                await update.message.reply_text(
                    f"🤷 В игре {game_code} пока нет участников.\n\n"
                    "Пригласите друзей командой:\n"
                    f"/join {game_code}"
                )
                return

            # Формируем сообщение
            participants_text = f"""
👥 Участники игры: {game_name}

🆔 Код: `{game_code}`
📅 Дата жеребьёвки: {draw_date}
👥 Участников: {current_participants} из {min_participants} мин.

Список участников:
"""

            # Добавляем информацию об участниках
            for i, participant in enumerate(participants, 1):
                participants_text += f"\n{format_participant_info(participant, i)}\n"

            # Добавляем подсказки для организатора
            if organizer_id == user_id and not self.db.is_game_drawn(game_code):
                participants_text += f"\n🎁 Для запуска жеребьёвки: /mix {game_code}"

            participants_text += f"\n💡 Для выхода из игры: /leave {game_code}"

            await update.message.reply_text(participants_text)

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /participants: {e}")
            await update.message.reply_text("❌ Ошибка при получении списка участников.")

    # === КОМАНДА MIX (ЖЕРЕБЬЁВКА) ===

    async def start_draw(self, update, context):
        """Запуск жеребьёвки"""
        try:
            user_id = update.effective_user.id

            # Если указан код игры в аргументах
            if context.args:
                game_code = context.args[0].upper()
            else:
                # Если код не указан, ищем игры где пользователь организатор
                user_games = self.db.get_user_active_games(user_id)
                organizer_games = [game for game in user_games if game[4] == user_id and not game[5]]

                if not organizer_games:
                    await update.message.reply_text(
                        "🤷 Вы не являетесь организатором ни одной игры, ожидающей жеребьёвки.\n\n"
                        "Создайте игру командой /create_game"
                    )
                    return

                if len(organizer_games) > 1:
                    games_list = "\n".join([
                        f"• `{game[0]}` - {game[1]} ({game[3]} участников)"
                        for game in organizer_games
                    ])

                    await update.message.reply_text(
                        f"🎮 Вы организатор нескольких игр:\n\n{games_list}\n\n"
                        "Для запуска жеребьёвки конкретной игры используйте:\n"
                        "/mix КОД_ИГРЫ\n\n"
                        "Пример: /mix ABC123"
                    )
                    return

                # Если игра одна - используем ее код
                game_code = organizer_games[0][0]

            # Проверяем, является ли пользователь организатором
            if not self.db.is_game_organizer(game_code, user_id):
                await update.message.reply_text(
                    "❌ Только организатор игры может запустить жеребьёвку!\n\n"
                    "Обратитесь к организатору игры."
                )
                return

            # Проверяем, не была ли уже проведена жеребьёвка
            if self.db.is_game_drawn(game_code):
                await update.message.reply_text(
                    "❌ Жеребьёвка для этой игры уже была проведена!\n\n"
                    "Невозможно провести жеребьёвку повторно."
                )
                return

            # Получаем информацию об игре
            game_info = self.db.get_game_info(game_code)
            if not game_info:
                await update.message.reply_text("❌ Игра не найдена.")
                return

            game_name, organizer_id, draw_date, min_participants, current_participants = game_info

            # Проверяем минимальное количество участников
            if current_participants < min_participants:
                await update.message.reply_text(
                    f"❌ Недостаточно участников для жеребьёвки!\n\n"
                    f"Требуется: {min_participants} участников\n"
                    f"Сейчас: {current_participants} участников\n\n"
                    f"Пригласите больше друзей командой:\n"
                    f"/join {game_code}"
                )
                return

            # Получаем ID участников
            participant_ids = self.db.get_game_participants_ids(game_code)

            if len(participant_ids) < 3:
                await update.message.reply_text(
                    "❌ Для жеребьёвки нужно минимум 3 участника!\n\n"
                    f"Сейчас участников: {len(participant_ids)}"
                )
                return

            # Запускаем жеребьёвку
            await update.message.reply_text(
                f"🎲 Запускаю жеребьёвку для игры '{game_name}'...\n\n"
                f"👥 Участников: {len(participant_ids)}\n"
                f"🔄 Распределяю пары..."
            )

            # Случайное распределение участников
            pairs = shuffle_participants(participant_ids)

            if not pairs:
                await update.message.reply_text("❌ Ошибка при распределении пар.")
                return

            # Сохраняем пары в базу
            success = self.db.assign_santa_pairs(game_code, pairs)

            if not success:
                await update.message.reply_text("❌ Ошибка при сохранении результатов жеребьёвки.")
                return

            # Отправляем сообщения каждому Санте
            sent_messages = 0
            failed_messages = 0

            for santa_id, recipient_id in pairs:
                recipient_info, wishlist = self.db.get_recipient_info(santa_id, game_code)

                if recipient_info:
                    full_name, bio = recipient_info

                    # Формируем сообщение для Санты
                    message = f"""🎅 Вы - Тайный Санта!

📛 Ваш получатель: {full_name}

📝 О получателе:
{bio or 'Информация не указана'}

🎁 Вишлист получателя:
"""

                    # Добавляем пункты вишлиста
                    if wishlist:
                        for item in wishlist:
                            item_name, description, photo_id = item
                            message += f"\n🎁 {item_name}"
                            if description and description != 'None':
                                message += f"\n   📝 {description}"
                    else:
                        message += "\n📝 Вишлист пуст"

                    message += f"\n\n💌 Вы можете отправить анонимное сообщение получателю командой: /message"
                    message += f"\n\n✨ Творите добро и дарите радость!"

                    # Отправляем сообщение Санте
                    try:
                        await context.bot.send_message(chat_id=santa_id, text=message)
                        sent_messages += 1
                        logger.info(f"✅ Сообщение отправлено Санте {santa_id}")
                    except Exception as e:
                        failed_messages += 1
                        logger.error(f"❌ Ошибка отправки сообщения Санте {santa_id}: {e}")

            # Отправляем отчет организатору
            report_message = f"""
✅ Жеребьёвка завершена успешно!

🎮 Игра: {game_name}
🆔 Код: {game_code}
👥 Участников: {len(pairs)}
📤 Сообщений отправлено: {sent_messages}
❌ Не отправлено: {failed_messages}

🎅 Все участники получили информацию о своих получателях!

✨ Желаем всем весёлого обмена подарками!
            """

            await update.message.reply_text(report_message)

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /mix: {e}")
            await update.message.reply_text("❌ Ошибка при запуске жеребьёвки.")

    # === КОМАНДА ДЛЯ ПРОСМОТРА ПОЛУЧАТЕЛЯ ===

    async def view_recipient(self, update, context):
        """Просмотр информации о получателе подарка"""
        try:
            user_id = update.effective_user.id

            # Если указан код игры в аргументах
            if context.args:
                game_code = context.args[0].upper()

                # Проверяем, участвует ли пользователь в игре
                if not self.db.is_user_in_game(user_id, game_code):
                    await update.message.reply_text(
                        f"❌ Вы не участвуете в игре {game_code}.\n\n"
                        "Присоединитесь к игре командой:\n"
                        f"/join {game_code}"
                    )
                    return
            else:
                # Если код не указан, ищем игры пользователя с жеребьевкой
                user_games = self.db.get_user_active_games(user_id)
                games_with_draw = [game for game in user_games if game[5]]  # game[5] - is_drawn

                if not games_with_draw:
                    await update.message.reply_text(
                        "🤷 У вас нет игр с проведенной жеребьёвкой.\n\n"
                        "Жеребьёвка необходима для просмотра информации о получателе."
                    )
                    return

                if len(games_with_draw) > 1:
                    games_list = "\n".join([
                        f"• `{game[0]}` - {game[1]} ({game[3]} участников)"
                        for game in games_with_draw
                    ])

                    await update.message.reply_text(
                        f"🎮 Вы участвуете в нескольких играх с жеребьёвкой:\n\n{games_list}\n\n"
                        "Для просмотра получателя конкретной игры используйте:\n"
                        "/my_recipient КОД_ИГРЫ\n\n"
                        "Пример: /my_recipient ABC123"
                    )
                    return

                # Если игра одна - используем ее код
                game_code = games_with_draw[0][0]

            # Проверяем, может ли пользователь просматривать получателя
            if not self.db.can_view_recipient(user_id, game_code):
                await update.message.reply_text(
                    "❌ Информация о получателе недоступна.\n\n"
                    "Возможные причины:\n"
                    "• Жеребьёвка еще не проведена\n"
                    "• У вас нет получателя в этой игре\n"
                    "• Вы организатор игры (организаторы не получают подарки)"
                )
                return

            # Получаем информацию о получателе
            recipient_pair = self.db.get_santa_pair(user_id, game_code)

            if not recipient_pair:
                await update.message.reply_text(
                    "❌ Не удалось найти информацию о вашем получателе.\n"
                    "Обратитесь к организатору игры."
                )
                return

            recipient_id, username, full_name, bio = recipient_pair

            # Получаем вишлист получателя
            wishlist = self.db.get_recipient_wishlist(recipient_id)

            # Получаем информацию об игре для красивого вывода
            game_info = self.db.get_game_info(game_code)
            game_name = game_info[0] if game_info else "Тайный Санта"

            # Формируем сообщение с информацией о получателе
            recipient_message = f"""
🎅 Ваш получатель подарка!

🎮 Игра: {game_name}
🆔 Код: {game_code}

👤 Получатель: {full_name or 'Имя не указано'}
📝 О себе:
{bio or 'Информация не указана'}

🎁 Вишлист получателя:
"""

            # Добавляем пункты вишлиста
            if wishlist:
                for i, item in enumerate(wishlist, 1):
                    item_name, description, photo_id = item
                    recipient_message += f"\n{i}. 🎁 {item_name}"
                    if description and description != 'None':
                        recipient_message += f"\n   📝 {description}"
            else:
                recipient_message += "\n📝 Вишлист пуст или не заполнен"

            recipient_message += f"""

💌 Вы можете отправить анонимное сообщение получателю командой: /message

✨ Творите добро и дарите радость!

💡 Эта информация также доступна по команде /my_recipient
"""

            await update.message.reply_text(recipient_message)

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /my_recipient: {e}")
            await update.message.reply_text("❌ Ошибка при получении информации о получателе.")

    # === КОМАНДЫ ДЛЯ АНОНИМНЫХ СООБЩЕНИЙ ===

    async def send_anonymous_message(self, update, context):
        """Начало отправки анонимного сообщения"""
        try:
            user_id = update.effective_user.id

            # Получаем игры пользователя с проведенной жеребьёвкой
            user_games = self.db.get_user_active_games(user_id)
            games_with_draw = [game for game in user_games if game[5]]  # game[5] - is_drawn

            if not games_with_draw:
                await update.message.reply_text(
                    "🤷 У вас нет игр с проведенной жеребьёвкой.\n\n"
                    "Жеребьёвка необходима для отправки анонимных сообщений."
                )
                return ConversationHandler.END

            # Сохраняем список игр в контексте
            context.user_data['available_games'] = games_with_draw

            if len(games_with_draw) == 1:
                # Если игра одна, сразу переходим к вводу сообщения
                game_code = games_with_draw[0][0]
                context.user_data['selected_game'] = game_code

                # Получаем получателя для этого Санты
                recipient_id = self.db.get_recipient_for_santa(user_id, game_code)

                if not recipient_id:
                    await update.message.reply_text(
                        "❌ Не удалось найти вашего получателя.\n"
                        "Возможно, жеребьёвка еще не завершена."
                    )
                    return ConversationHandler.END

                recipient_info = self.db.get_user(recipient_id)
                if recipient_info:
                    recipient_name = recipient_info[2] or "Неизвестный"

                    await update.message.reply_text(
                        f"✉️ Вы готовы отправить анонимное сообщение вашему получателю:\n"
                        f"🎁 {recipient_name}\n\n"
                        f"Введите ваше сообщение:\n\n"
                        f"❌ Для отмены отправьте /cancel"
                    )
                    return MESSAGE_TEXT
                else:
                    await update.message.reply_text(
                        "❌ Не удалось найти информацию о получателе."
                    )
                    return ConversationHandler.END

            # Если игр несколько, показываем список для выбора
            games_list = "\n".join([
                f"{i + 1}. {game[1]} (код: {game[0]})"
                for i, game in enumerate(games_with_draw)
            ])

            await update.message.reply_text(
                f"🎮 Выберите игру для отправки сообщения:\n\n{games_list}\n\n"
                f"Отправьте номер игры (1, 2, 3...):\n\n"
                f"❌ Для отмены отправьте /cancel"
            )
            return MESSAGE_GAME_SELECT

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /message: {e}")
            await update.message.reply_text("❌ Ошибка при отправке сообщения.")
            return ConversationHandler.END

    async def select_message_game(self, update, context):
        """Выбор игры для отправки сообщения"""
        try:
            user_id = update.effective_user.id
            choice_text = update.message.text

            if not choice_text.isdigit():
                await update.message.reply_text(
                    "❌ Пожалуйста, введите номер игры (1, 2, 3...):"
                )
                return MESSAGE_GAME_SELECT

            choice = int(choice_text) - 1
            available_games = context.user_data.get('available_games', [])

            if choice < 0 or choice >= len(available_games):
                await update.message.reply_text(
                    f"❌ Неверный номер. Выберите от 1 до {len(available_games)}:"
                )
                return MESSAGE_GAME_SELECT

            selected_game = available_games[choice]
            game_code = selected_game[0]
            context.user_data['selected_game'] = game_code

            # Получаем получателя для этого Санты
            recipient_id = self.db.get_recipient_for_santa(user_id, game_code)

            if not recipient_id:
                await update.message.reply_text(
                    "❌ Не удалось найти вашего получателя.\n"
                    "Возможно, жеребьёвка еще не завершена."
                )
                return ConversationHandler.END

            recipient_info = self.db.get_user(recipient_id)
            if recipient_info:
                recipient_name = recipient_info[2] or "Неизвестный"

                await update.message.reply_text(
                    f"✉️ Вы готовы отправить анонимное сообщение вашему получателю:\n"
                    f"🎁 {recipient_name}\n\n"
                    f"Введите ваше сообщение:\n\n"
                    f"❌ Для отмены отправьте /cancel"
                )
                return MESSAGE_TEXT
            else:
                await update.message.reply_text(
                    "❌ Не удалось найти информацию о получателе."
                )
                return ConversationHandler.END

        except Exception as e:
            logger.error(f"❌ Ошибка в select_message_game: {e}")
            await update.message.reply_text("❌ Ошибка при выборе игры.")
            return ConversationHandler.END

    async def send_message_text(self, update, context):
        """Отправка текста анонимного сообщения"""
        try:
            user_id = update.effective_user.id
            message_text = update.message.text
            game_code = context.user_data.get('selected_game')

            if not game_code:
                await update.message.reply_text("❌ Ошибка: игра не выбрана.")
                return ConversationHandler.END

            # Получаем получателя
            recipient_id = self.db.get_recipient_for_santa(user_id, game_code)

            if not recipient_id:
                await update.message.reply_text("❌ Не удалось найти получателя.")
                return ConversationHandler.END

            # Проверяем, может ли пользователь отправить сообщение
            if not self.db.can_send_message(user_id, recipient_id, game_code):
                await update.message.reply_text(
                    "❌ Вы не можете отправить сообщение этому пользователю.\n"
                    "Возможно, вы не являетесь его Тайным Сантой."
                )
                return ConversationHandler.END

            # Сохраняем сообщение
            success = self.db.add_anonymous_message(game_code, user_id, recipient_id, message_text)

            if success:
                # Получаем информацию о получателе для подтверждения
                recipient_info = self.db.get_user(recipient_id)
                recipient_name = recipient_info[2] or "Неизвестный" if recipient_info else "Неизвестный"

                await update.message.reply_text(
                    f"✅ Ваше анонимное сообщение отправлено получателю:\n"
                    f"🎁 {recipient_name}\n\n"
                    f"💌 Сообщение: {message_text}\n\n"
                    f"📨 Получатель увидит его при проверке сообщений командой /messages"
                )

                # Оповещаем получателя о новом сообщении (если он в боте)
                try:
                    game_info = self.db.get_game_info(game_code)
                    game_name = game_info[0] if game_info else "Тайный Санта"

                    notification = f"""
📨 У вас новое анонимное сообщение!

🎮 Игра: {game_name}
💌 Используйте /messages чтобы прочитать его

✨ Ваш Тайный Санта хочет что-то уточнить!
                    """
                    await context.bot.send_message(chat_id=recipient_id, text=notification)
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление получателю {recipient_id}: {e}")
            else:
                await update.message.reply_text("❌ Ошибка при отправке сообщения.")

            # Очищаем временные данные
            context.user_data.clear()

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"❌ Ошибка в send_message_text: {e}")
            await update.message.reply_text("❌ Ошибка при отправке сообщения.")
            return ConversationHandler.END

    async def check_messages(self, update, context):
        """Проверка непрочитанных сообщений"""
        try:
            user_id = update.effective_user.id

            # Получаем непрочитанные сообщения
            unread_messages = self.db.get_unread_messages(user_id)

            if not unread_messages:
                await update.message.reply_text(
                    "📭 У вас нет непрочитанных сообщений.\n\n"
                    "Сообщения появятся здесь, когда ваш Тайный Санта захочет с вами связаться!"
                )
                return

            await update.message.reply_text(
                f"📨 У вас {len(unread_messages)} непрочитанных сообщений:\n\n"
                f"Читаю сообщения..."
            )

            # Отправляем каждое сообщение
            for message_id, message_text, sent_at, game_code in unread_messages:
                # Получаем информацию об игре
                game_info = self.db.get_game_info(game_code)
                game_name = game_info[0] if game_info else "Неизвестная игра"

                # Форматируем дату
                try:
                    date_obj = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%d.%m.%Y %H:%M")
                except:
                    formatted_date = sent_at

                message_display = f"""
💌 Анонимное сообщение:

🎮 Игра: {game_name}
📅 Дата: {formatted_date}
💬 Сообщение:
{message_text}

✨ Ваш Тайный Санта
                """

                await update.message.reply_text(message_display)

                # Помечаем сообщение как прочитанное
                self.db.mark_message_as_read(message_id)

            await update.message.reply_text(
                "✅ Все сообщения прочитаны!\n\n"
                "💡 Чтобы ответить вашему Санте, просто попросите его отправить вам новое сообщение "
                "через команду /message - все сообщения анонимны!"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка в команде /messages: {e}")
            await update.message.reply_text("❌ Ошибка при проверке сообщений.")

    async def cancel(self, update, context):
        """Отмена операции"""
        try:
            context.user_data.clear()
            await update.message.reply_text("❌ Операция отменена.")
            return ConversationHandler.END

        except Exception as e:
            logger.error(f"❌ Ошибка в cancel: {e}")
            return ConversationHandler.END

    def setup_handlers(self):
        """Настройка всех обработчиков"""

        # ConversationHandler для профиля
        profile_conv = ConversationHandler(
            entry_points=[CommandHandler('profile', self.profile)],
            states={
                PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_profile)],
                BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_bio)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        # ConversationHandler для создания игры
        game_conv = ConversationHandler(
            entry_points=[CommandHandler('create_game', self.create_game)],
            states={
                GAME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_game_name)],
                GAME_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_game_date)],
                GAME_MIN_PARTICIPANTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_min_participants)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        # ConversationHandler для анонимных сообщений
        message_conv = ConversationHandler(
            entry_points=[CommandHandler('message', self.send_anonymous_message)],
            states={
                MESSAGE_GAME_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_message_game)],
                MESSAGE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_message_text)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        # Базовые команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("join", self.join_game))
        self.application.add_handler(CommandHandler("leave", self.leave_game))
        self.application.add_handler(CommandHandler("status", self.game_status))
        self.application.add_handler(CommandHandler("participants", self.show_participants))
        self.application.add_handler(CommandHandler("mix", self.start_draw))
        self.application.add_handler(CommandHandler("messages", self.check_messages))
        self.application.add_handler(CommandHandler("my_recipient", self.view_recipient))  # НОВАЯ КОМАНДА

        # Conversation handlers
        self.application.add_handler(profile_conv)
        self.application.add_handler(game_conv)
        self.application.add_handler(message_conv)

    def run(self):
        """Запуск бота"""
        logger.info("🎅 Secret Santa Bot запускается...")
        print("✅ Бот запущен! Нажмите Ctrl+C для остановки.")
        self.application.run_polling()