import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import random
import string
from database import get_db_session, User, Game, Participant, SantaPair, WishlistItem
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    try:
        # Создаем Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("create_game", create_game))
        application.add_handler(CommandHandler("status", game_status))
        application.add_handler(CommandHandler("join", join_game))
        application.add_handler(CommandHandler("leave", leave_game))
        application.add_handler(CommandHandler("mix", mix_pairs))
        application.add_handler(CommandHandler("my_recipient", my_recipient))
        
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Запускаем бота
        print("Бот запускается...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    db = get_db_session()
    
    try:
        existing_user = db.query(User).filter_by(telegram_id=user.id).first()
        
        if not existing_user:
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
                "/create_game - Создать новую игру\n"
                "/join [код] - Присоединиться к игре\n"
                "/help - Полная справка"
            )
        else:
            welcome_message = f"С возвращением, {user.full_name}! 🎄"
        
        await update.message.reply_text(welcome_message)
        
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text("Произошла ошибка.")
    finally:
        db.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
🎅 Тайный Санта - Справка по командам:

/start - Регистрация и начало работы
/create_game - Создать новую игру
/join [код] - Присоединиться к игре
/status - Статус игры (для организатора)
/mix - Провести жеребьевку
/my_recipient - Посмотреть информацию о получателе
/leave - Выйти из игры

Просто отправьте текст - добавить в вишлист
Отправьте фото - добавить фото в вишлист
    """
    await update.message.reply_text(help_text)

async def create_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание новой игры"""
    db = get_db_session()
    user = update.effective_user
    
    try:
        db_user = db.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            await update.message.reply_text("Сначала зарегистрируйтесь с помощью /start")
            return
        
        # Генерируем уникальный код
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
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
            f"Код для приглашения: `{code}`\n"
            f"Название: {new_game.name}\n"
            f"Дата жеребьевки: {new_game.draw_date.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Отправьте этот код участникам!"
        )
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in create_game: {e}")
        await update.message.reply_text("Ошибка при создании игры.")
    finally:
        db.close()

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединение к игре"""
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
        
        await update.message.reply_text(
            f"✅ Вы присоединились к игре \"{game.name}\"!\n\n"
            f"Жеребьевка: {game.draw_date.strftime('%d.%m.%Y %H:%M')}"
        )
        
    except Exception as e:
        logger.error(f"Error in join_game: {e}")
        await update.message.reply_text("Ошибка при присоединении.")
    finally:
        db.close()

async def game_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус игры"""
    db = get_db_session()
    user = update.effective_user
    
    try:
        db_user = db.query(User).filter_by(telegram_id=user.id).first()
        organized_games = db.query(Game).filter_by(organizer_id=db_user.id).all()
        
        if not organized_games:
            await update.message.reply_text("Вы не организуете игр. Используйте /create_game")
            return
        
        message = "🎮 Ваши игры:\n\n"
        for game in organized_games:
            participants = db.query(Participant).filter_by(game_id=game.id).all()
            status = "✅ Завершена" if game.is_completed else "🔄 Активна"
            
            message += (
                f"{game.name} ({status})\n"
                f"Код: {game.code}\n"
                f"Участников: {len(participants)}\n"
                f"Жеребьевка: {game.draw_date.strftime('%d.%m.%Y')}\n\n"
            )
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in game_status: {e}")
    finally:
        db.close()

async def mix_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проведение жеребьевки"""
    db = get_db_session()
    user = update.effective_user
    
    try:
        db_user = db.query(User).filter_by(telegram_id=user.id).first()
        games = db.query(Game).filter_by(organizer_id=db_user.id, is_completed=False).all()
        
        if not games:
            await update.message.reply_text("У вас нет активных игр.")
            return
        
        game = games[0]
        participants = db.query(Participant).filter_by(game_id=game.id).all()
        
        if len(participants) < 3:
            await update.message.reply_text("Нужно минимум 3 участника для жеребьевки.")
            return
        
        # Создаем пары
        participant_ids = [p.user_id for p in participants]
        random.shuffle(participant_ids)
        
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
        
        game.is_completed = True
        db.commit()
        
        # Уведомляем участников
        for pair in pairs:
            santa_user = db.query(User).filter_by(id=pair.santa_id).first()
            recipient_user = db.query(User).filter_by(id=pair.recipient_id).first()
            
            message = f"🎅 Вам выпал: {recipient_user.full_name or recipient_user.username}"
            
            try:
                await context.bot.send_message(
                    chat_id=santa_user.telegram_id,
                    text=message
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение {santa_user.telegram_id}: {e}")
        
        await update.message.reply_text(f"✅ Жеребьевка завершена! Участники уведомлены.")
        
    except Exception as e:
        logger.error(f"Error in mix_pairs: {e}")
        await update.message.reply_text("Ошибка при жеребьевке.")
    finally:
        db.close()

async def my_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр получателя"""
    db = get_db_session()
    user = update.effective_user
    
    try:
        db_user = db.query(User).filter_by(telegram_id=user.id).first()
        pairs = db.query(SantaPair).filter_by(santa_id=db_user.id).all()
        
        if not pairs:
            await update.message.reply_text("У вас нет активных пар.")
            return
        
        for pair in pairs:
            recipient_user = db.query(User).filter_by(id=pair.recipient_id).first()
            await update.message.reply_text(
                f"🎅 Ваш получатель: {recipient_user.full_name or recipient_user.username}"
            )
        
    except Exception as e:
        logger.error(f"Error in my_recipient: {e}")
    finally:
        db.close()

async def leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из игры"""
    db = get_db_session()
    user = update.effective_user
    
    try:
        db_user = db.query(User).filter_by(telegram_id=user.id).first()
        participants = db.query(Participant).filter_by(user_id=db_user.id).all()
        
        if not participants:
            await update.message.reply_text("Вы не участвуете в играх.")
            return
        
        participant = participants[0]
        game = db.query(Game).filter_by(id=participant.game_id).first()
        
        db.delete(participant)
        db.commit()
        
        await update.message.reply_text(f"✅ Вы вышли из игры \"{game.name}\"")
        
    except Exception as e:
        logger.error(f"Error in leave_game: {e}")
    finally:
        db.close()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    db = get_db_session()
    user = update.effective_user
    
    try:
        db_user = db.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            return
        
        text = update.message.text
        
        wishlist_item = WishlistItem(
            user_id=db_user.id,
            title=text[:100],
            description=text
        )
        db.add(wishlist_item)
        db.commit()
        
        await update.message.reply_text("✅ Добавлено в вишлист!")
    
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
    finally:
        db.close()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото"""
    db = get_db_session()
    user = update.effective_user
    
    try:
        db_user = db.query(User).filter_by(telegram_id=user.id).first()
        
        if not db_user:
            return
        
        photo = update.message.photo[-1]
        caption = update.message.caption or "Фото из вишлиста"
        
        wishlist_item = WishlistItem(
            user_id=db_user.id,
            title=caption[:100],
            description=caption,
            photo_id=photo.file_id
        )
        db.add(wishlist_item)
        db.commit()
        
        await update.message.reply_text("✅ Фото добавлено в вишлист!")
    
    except Exception as e:
        logger.error(f"Error in handle_photo: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    main()