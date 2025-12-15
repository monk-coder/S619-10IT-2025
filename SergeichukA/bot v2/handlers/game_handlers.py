from telebot import types
from bot_instance import bot
from utils import log_action, set_step
from models import ensure_user, create_game, find_game_by_code, add_participant, remove_participant, list_participants, get_profile, get_games_for_owner, get_participating_games, get_match, store_matches, list_wishlist, Game
import random
from database import DB, DB_LOCK
from models import now_ts

# Быстрые функции-помощники
def get_user_display(uid):
    profile = get_profile(uid)
    return profile["full_name"] or profile["username"] or f"ID{uid}"

def format_game_info(game):
    participants = list_participants(game.id)
    base = f"<b>{game.title}</b> (код <code>{game.code}</code>) — {len(participants)} участников"
    if participants:
        names = [get_user_display(uid) for uid in participants]
        return f"{base}\nУчастники: {', '.join(names)}"
    return base

# Обработчики команд
def setup_game_handlers():
    @bot.message_handler(commands=["create_game"])
    def cmd_create_game(message):
        ensure_user(message.from_user.id, message.from_user.username)
        set_step(message.from_user.id, "game_title", {})
        bot.send_message(message.chat.id, "🎲 Введите название игры:")

    @bot.message_handler(commands=["status"])
    def cmd_status(message):
        games = get_games_for_owner(message.from_user.id)
        if not games:
            bot.send_message(message.chat.id, "Нет созданных игр")
            return
        bot.send_message(message.chat.id, "\n\n".join(format_game_info(game) for game in games))

    @bot.message_handler(commands=["join", "leave", "participants", "mix", "send"])
    def handle_code_commands(message):
        parts = message.text.split()
        if len(parts) < 2:
            set_step(message.from_user.id, f"{parts[0][1:]}_code", {})
            bot.send_message(message.chat.id, f"Введите код игры:")
            return
        
        code = parts[1]
        handlers = {
            "join": join_game,
            "leave": leave_game, 
            "participants": show_participants,
            "mix": mix_game,
            "send": mix_game
        }
        handlers[parts[0][1:]](message, code)

    @bot.message_handler(commands=["my_recipient"])
    def cmd_my_recipient(message):
        games = get_participating_games(message.from_user.id)
        matches = []
        for game in games:
            recipient = get_match(game.id, message.from_user.id)
            if recipient:
                profile = get_profile(recipient)
                wishlist = list_wishlist(recipient)
                info = f"<b>{game.title}</b>\nФИО: {profile['full_name'] or 'не указано'}\nО себе: {profile['bio'] or 'не указано'}"
                if wishlist:
                    info += "\nВишлист:\n" + "\n".join(f"• {item['description']}" for item in wishlist)
                matches.append(info)
        bot.send_message(message.chat.id, "\n\n".join(matches) if matches else "Нет получателей")

    @bot.message_handler(commands=["ask"])
    def cmd_ask(message):
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Напишите вопрос: /ask текст")
            return
        
        sent = 0
        for game in get_participating_games(message.from_user.id):
            recipient = get_match(game.id, message.from_user.id)
            if recipient:
                bot.send_message(recipient, f"<b>Вопрос от Санты ({game.title}):</b>\n{parts[1]}")
                with DB_LOCK:
                    DB.execute("INSERT INTO anonymous_questions VALUES (?, ?, ?, ?, ?)", 
                              (game.id, message.from_user.id, recipient, parts[1], now_ts()))
                    DB.commit()
                sent += 1
        bot.send_message(message.chat.id, "Вопрос отправлен" if sent else "Нет получателей")

# Базовые операции с играми
def join_game(message, code):
    game = find_game_by_code(code)
    if not game:
        bot.send_message(message.chat.id, "Игра не найдена")
        return
    
    if add_participant(game.id, message.from_user.id):
        bot.send_message(message.chat.id, f"🎉 Присоединились к игре <b>{game.title}</b>!")
    else:
        bot.send_message(message.chat.id, "Уже участвуете")

def leave_game(message, code):
    game = find_game_by_code(code)
    if not game:
        bot.send_message(message.chat.id, "Игра не найдена")
        return
    
    if remove_participant(game.id, message.from_user.id):
        bot.send_message(message.chat.id, "🚪 Вышли из игры")
    else:
        bot.send_message(message.chat.id, "Не удалось выйти")

def show_participants(message, code):
    game = find_game_by_code(code)
    if not game:
        bot.send_message(message.chat.id, "Игра не найдена")
        return
    
    participants = list_participants(game.id)
    if not participants:
        bot.send_message(message.chat.id, "Нет участников")
        return
    
    lines = [f"<b>{game.title}</b>:"] + [get_user_display(uid) for uid in participants]
    bot.send_message(message.chat.id, "\n".join(lines))

def mix_game(message, code):
    game = find_game_by_code(code)
    if not game:
        bot.send_message(message.chat.id, "Игра не найдена")
        return
    
    if message.from_user.id != game.owner_id:
        bot.send_message(message.chat.id, "Только организатор может проводить жеребьёвку")
        return
    
    participants = list_participants(game.id)
    if len(participants) < max(3, game.min_participants):
        bot.send_message(message.chat.id, "Недостаточно участников")
        return
    
    # Жеребьёвка
    shuffled = participants[:]
    random.shuffle(shuffled)
    recipients = shuffled[1:] + shuffled[:1]
    pairs = dict(zip(shuffled, recipients))
    
    store_matches(game.id, pairs)
    bot.send_message(message.chat.id, "🎉 Жеребьёвка проведена!")
    
    # Уведомления
    for santa_id, recipient_id in pairs.items():
        profile = get_profile(recipient_id)
        wishlist = list_wishlist(recipient_id)
        msg = f"🎅 Вы Тайный Санта в <b>{game.title}</b>!\n🎁 Получатель:\nФИО: {profile['full_name'] or 'не указано'}\nО себе: {profile['bio'] or 'не указано'}"
        if wishlist:
            msg += "\n🎉 Вишлист:\n" + "\n".join(f"• {item['description']}" for item in wishlist)
        bot.send_message(santa_id, msg)
