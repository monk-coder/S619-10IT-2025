import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError
from datetime import datetime, timedelta
import random
import string
import asyncio
from database import get_db_session, User, Game, Participant, SantaPair, WishlistItem, AnonymousQuestion
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SecretSantaBot:
    def __init__(self):
        try:
            self.application = Application.builder().token(BOT_TOKEN).build()
            self.setup_handlers()
        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
            raise

    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Основные команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("profile", self.profile))
        self.application.add_handler(CommandHandler("create_game", self.create_game))
        self.application.add_handler(CommandHandler("status", self.game_status))
        self.application.add_handler(CommandHandler("join", self.join_game))
        self.application.add_handler(CommandHandler("leave", self.leave_game))
        self.application.add_handler(CommandHandler("mix", self.mix_pairs))
        self.application.add_handler(CommandHandler("send", self.mix_pairs))
        self.application.add_handler(CommandHandler("my_recipient", self.my_recipient))
        
        # Обработчики сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start - регистрация пользователя"""
        user = update.effective_user
        db = get_db_session()
        
        try:
            # Проверяем, есть ли пользователь в базе
            existing_user = db.query(User).filter_by(telegram_id=user.id).first()
            
            if not existing_user:
                # Создаем нового пользователя
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    full_name=user.full_name
                )
                db.add(new_user)
                db.commit()
                welcome_message = (
                    "🎅 Добро пожаловать в Тайного Санту!\n\n"
                    "Я помогу вам организовать обмен подарками.\n\n"
                    "Основные команды:\n"
                    "/profile - Настроить профиль\n"
                    "/create_game - Создать новую игру\n"
                    "/join - Присоединиться к игре\n"
                    "/help - Полная справка по командам"
                )
            else:
                welcome_message = (
                    f"С возвращением, {user.full_name}! 🎄\n\n"
                    "Используйте /help для просмотра всех команд."
                )
            
            await update.message.reply_text(welcome_message)
            
        except Exception as e:
            logger.error(f"Error in start: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
        finally:
            db.close()

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help - справка по всем командам"""
        help_text = """
🎅 Тайный Санта - Справка по командам 🎅

Личный кабинет:
/start - Регистрация и начало работы
/profile - Настройка профиля и вишлиста
/my_recipient - Посмотреть информацию о вашем получателе

Создание и управление игрой:
/create_game - Создать новую игру
/status - Статус текущей игры (для организатора)
/mix или /send - Провести жеребьевку

Участие в играх:
/join [код] - Присоединиться к игре
/leave - Выйти из текущей игры

Дополнительные функции:
Отправьте текстовое сообщение - добавить пункт в вишлист
Отправьте фото с подписью - добавить фото в вишлист
        """
        await update.message.reply_text(help_text)

    async def create_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /create_game - создание новой игры"""
        db = get_db_session()
        user = update.effective_user
        
        try:
            db_user = db.query(User).filter_by(telegram_id=user.id).first()
            
            if not db_user:
                await update.message.reply_text("Сначала зарегистрируйтесь с помощью /start")
                return
            
            # Генерируем уникальный код игры
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            # Создаем игру с дефолтными параметрами
            new_game = Game(
                code=code,
                name="Тайный Санта",
                organizer_id=db_user.id,
                draw_date=datetime.now() + timedelta(days=7),
                min_participants=3
            )
            db.add(new_game)
            db.commit()
            
            # Добавляем организатора как участника
            participant = Participant(game_id=new_game.id, user_id=db_user.id)
            db.add(participant)
            db.commit()
            
            message = (
                f"🎮 Игра создана!\n\n"
                f"Код для приглашения: {code}\n"
                f"Название: {new_game.name}\n"
                f"Дата жеребьевки: {new_game.draw_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"Минимальное количество участников: {new_game.min_participants}\n\n"
                f"Отправьте код участникам для присоединения!\n"
                f"Используйте /status для просмотра участников."
            )
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in create_game: {e}")
            await update.message.reply_text("Произошла ошибка при создании игры.")
        finally:
            db.close()

    async def join_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /join - присоединение к игре"""
        if not context.args:
            await update.message.reply_text("Использование: /join КОД_ИГРЫ")
            return
        
        game_code = context.args[0].upper()
        db = get_db_session()
        user = update.effective_user
        
        try:
            db_user = db.query(User).filter_by(telegram_id=user.id).first()
            game = db.query(Game).filter_by(code=game_code).first()
            
            if not game:
                await update.message.reply_text("Игра с таким кодом не найдена.")
                return
            
            if game.is_completed:
                await update.message.reply_text("Эта игра уже завершена.")
                return
            
            # Проверяем, не участвует ли уже пользователь
            existing_participant = db.query(Participant).filter_by(
                game_id=game.id, user_id=db_user.id
            ).first()
            
            if existing_participant:
                await update.message.reply_text("Вы уже участвуете в этой игре.")
                return
            
            # Добавляем участника
            participant = Participant(game_id=game.id, user_id=db_user.id)
            db.add(participant)
            db.commit()
            
            # Получаем количество участников
            participants_count = db.query(Participant).filter_by(game_id=game.id).count()
            
            await update.message.reply_text(
                f"✅ Вы успешно присоединились к игре!\n\n"
                f"Название: {game.name}\n"
                f"Участников: {participants_count}\n"
                f"Жеребьевка: {game.draw_date.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Не забудьте настроить вишлист командой /profile!"
            )
            
        except Exception as e:
            logger.error(f"Error in join_game: {e}")
            await update.message.reply_text("Произошла ошибка при присоединении к игре.")
        finally:
            db.close()

    async def game_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status - статус игры"""
        db = get_db_session()
        user = update.effective_user
        
        try:
            db_user = db.query(User).filter_by(telegram_id=user.id).first()
            
            # Находим игры, где пользователь организатор
            organized_games = db.query(Game).filter_by(organizer_id=db_user.id).all()
            
            if not organized_games:
                await update.message.reply_text(
                    "Вы не организуете ни одной игры. "
                    "Создайте игру с помощью /create_game"
                )
                return
            
            message = "🎮 Ваши игры:\n\n"
            
            for game in organized_games:
                participants = db.query(Participant).filter_by(game_id=game.id).all()
                participant_names = []
                
                for participant in participants:
                    participant_names.append(participant.user.full_name or participant.user.username)
                
                status = "✅ Завершена" if game.is_completed else "🔄 Активна"
                
                message += (
                    f"{game.name} ({status})\n"
                    f"Код: {game.code}\n"
                    f"Участников: {len(participants)}\n"
                    f"Жеребьевка: {game.draw_date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Участники: {', '.join(participant_names)}\n\n"
                )
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in game_status: {e}")
            await update.message.reply_text("Произошла ошибка.")
        finally:
            db.close()

    async def mix_pairs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /mix или /send - проведение жеребьевки"""
        db = get_db_session()
        user = update.effective_user
        
        try:
            db_user = db.query(User).filter_by(telegram_id=user.id).first()
            
            # Находим игры, где пользователь организатор и жеребьевка еще не проведена
            games = db.query(Game).filter_by(organizer_id=db_user.id, is_completed=False).all()
            
            if not games:
                await update.message.reply_text(
                    "У вас нет активных игр или вы не являетесь организатором."
                )
                return
            
            # Для простоты берем первую найденную игру
            game = games[0]
            participants = db.query(Participant).filter_by(game_id=game.id).all()
            
            if len(participants) < game.min_participants:
                await update.message.reply_text(
                    f"Недостаточно участников. Минимум: {game.min_participants}, сейчас: {len(participants)}"
                )
                return
            
            # Создаем список для жеребьевки
            participant_ids = [p.user_id for p in participants]
            random.shuffle(participant_ids)
            
            # Создаем пары Санта -> Получатель
            pairs = []
            for i in range(len(participant_ids)):
                santa_id = participant_ids[i]
                recipient_id = participant_ids[(i + 1) % len(participant_ids)]
                
                pair = SantaPair(
                    game_id=game.id,
                    santa_id=santa_id,
                    recipient_id=recipient_id
                )
                pairs.append(pair)
                db.add(pair)
            
            # Помечаем игру как завершенную
            game.is_completed = True
            db.commit()
            
            # Отправляем сообщения участникам
            for pair in pairs:
                santa_user = db.query(User).filter_by(id=pair.santa_id).first()
                recipient_user = db.query(User).filter_by(id=pair.recipient_id).first()
                
                # Формируем сообщение для Санты
                recipient_info = (
                    f"🎅 Вам выпал: {recipient_user.full_name or recipient_user.username}\n\n"
                )
                
                if recipient_user.bio:
                    recipient_info += f"О себе: {recipient_user.bio}\n\n"
                
                # Добавляем вишлист получателя
                wishlist_items = db.query(WishlistItem).filter_by(user_id=recipient_user.id).all()
                if wishlist_items:
                    recipient_info += "🎁 Вишлист:\n"
                    for item in wishlist_items:
                        recipient_info += f"• {item.title}"
                        if item.description:
                            recipient_info += f" - {item.description}"
                        recipient_info += "\n"
                
                # Отправляем сообщение Санте
                try:
                    await context.bot.send_message(
                        chat_id=santa_user.telegram_id,
                        text=recipient_info
                    )
                    
                    # Отправляем фото из вишлиста, если есть
                    for item in wishlist_items:
                        if item.photo_id:
                            await context.bot.send_photo(
                                chat_id=santa_user.telegram_id,
                                photo=item.photo_id,
                                caption=f"📸 {item.title}"
                            )
                
                except Exception as e:
                    logger.error(f"Error sending message to {santa_user.telegram_id}: {e}")
            
            await update.message.reply_text(
                f"✅ Жеребьевка завершена! Все участники получили свои пары.\n"
                f"Всего распределено: {len(pairs)} пар"
            )
            
        except Exception as e:
            logger.error(f"Error in mix_pairs: {e}")
            await update.message.reply_text("Произошла ошибка при жеребьевке.")
        finally:
            db.close()

    async def my_recipient(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /my_recipient - просмотр информации о получателе"""
        db = get_db_session()
        user = update.effective_user
        
        try:
            db_user = db.query(User).filter_by(telegram_id=user.id).first()
            
            # Находим активные пары, где пользователь - Санта
            pairs = db.query(SantaPair).filter_by(santa_id=db_user.id).all()
            
            if not pairs:
                await update.message.reply_text(
                    "У вас нет активных пар. Возможно, жеребьевка еще не проводилась."
                )
                return
            
            for pair in pairs:
                recipient_user = db.query(User).filter_by(id=pair.recipient_id).first()
                game = db.query(Game).filter_by(id=pair.game_id).first()
                
                recipient_info = (
                    f"🎅 Ваш получатель в игре \"{game.name}\":\n"
                    f"Имя: {recipient_user.full_name or recipient_user.username}\n\n"
                )
                
                if recipient_user.bio:
                    recipient_info += f"О себе: {recipient_user.bio}\n\n"
                
                # Вишлист получателя
                wishlist_items = db.query(WishlistItem).filter_by(user_id=recipient_user.id).all()
                if wishlist_items:
                    recipient_info += "🎁 Вишлист:\n"
                    for item in wishlist_items:
                        recipient_info += f"• {item.title}"
                        if item.description:
                            recipient_info += f" - {item.description}"
                        recipient_info += "\n"
                
                await update.message.reply_text(recipient_info)
                
                # Отправляем фото из вишлиста
                for item in wishlist_items:
                    if item.photo_id:
                        await update.message.reply_photo(
                            photo=item.photo_id,
                            caption=f"📸 {item.title}"
                        )
            
        except Exception as e:
            logger.error(f"Error in my_recipient: {e}")
            await update.message.reply_text("Произошла ошибка.")
        finally:
            db.close()

    async def leave_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /leave - выход из игры"""
        db = get_db_session()
        user = update.effective_user
        
        try:
            db_user = db.query(User).filter_by(telegram_id=user.id).first()
            
            # Находим активные участия пользователя
            participants = db.query(Participant).filter_by(user_id=db_user.id).all()
            
            if not participants:
                await update.message.reply_text("Вы не участвуете ни в одной игре.")
                return
            
            # Для простоты выходим из первой найденной игры
            participant = participants[0]
            game = db.query(Game).filter_by(id=participant.game_id).first()
            
            db.delete(participant)
            db.commit()
            
            await update.message.reply_text(
                f"✅ Вы вышли из игры \"{game.name}\""
            )
            
        except Exception as e:
            logger.error(f"Error in leave_game: {e}")
            await update.message.reply_text("Произошла ошибка при выходе из игры.")
        finally:
            db.close()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений - добавление в вишлист"""
        db = get_db_session()
        user = update.effective_user
        
        try:
            db_user = db.query(User).filter_by(telegram_id=user.id).first()
            
            if not db_user:
                await update.message.reply_text("Сначала зарегистрируйтесь с помощью /start")
                return
            
            text = update.message.text
            
            # Добавляем текст как пункт вишлиста
            wishlist_item = WishlistItem(
                user_id=db_user.id,
                title=text[:100],
                description=text
            )
            db.add(wishlist_item)
            db.commit()
            
            await update.message.reply_text(
                "✅ Пункт добавлен в ваш вишлист!\n"
                "Вы можете прикрепить фото к этому пункту, отправив его как подпись к следующему фото."
            )
        
        except Exception as e:
            logger.error(f"Error in handle_message: {e}")
        finally:
            db.close()

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фото - добавление в вишлист"""
        db = get_db_session()
        user = update.effective_user
        
        try:
            db_user = db.query(User).filter_by(telegram_id=user.id).first()
            
            if not db_user:
                await update.message.reply_text("Сначала зарегистрируйтесь с помощью /start")
                return
            
            photo = update.message.photo[-1]
            caption = update.message.caption or "Фото из вишлиста"
            
            # Добавляем фото в вишлист
            wishlist_item = WishlistItem(
                user_id=db_user.id,
                title=caption[:100],
                description=caption,
                photo_id=photo.file_id
            )
            db.add(wishlist_item)
            db.commit()
            
            await update.message.reply_text(
                "✅ Фото добавлено в ваш вишлист!"
            )
        
        except Exception as e:
            logger.error(f"Error in handle_photo: {e}")
        finally:
            db.close()

    def run(self):
        """Запуск бота"""
        self.application.run_polling()

if __name__ == '__main__':
    bot = SecretSantaBot()
    bot.run()