"""Обработчики игр."""
import random
from typing import Dict, List

from telebot import types

from bot.bot import bot, send_game_menu, send_main_menu
from database import operations
from utils.helpers import log_action, set_step, ensure_owner, notify_pairs

def start_create_game_flow(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "game_title", {})
    log_action("start_create_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎄 Введите название для новой игры:")

def send_owner_status(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    log_action("view_owner_status", user_id=message.from_user.id)
    games = operations.get_games_for_owner(message.from_user.id)
    
    if not games:
        bot.send_message(message.chat.id, "📭 У вас пока нет созданных игр.")
        return
    
    lines = ["📋 <b>Ваши игры:</b>", ""]
    
    for game in games:
        participants = operations.list_participants(game.id)
        lines.append(f"🎄 <b>{game.title}</b>")
        lines.append(f"   🔑 Код: <code>{game.code}</code>")
        lines.append(f"   👥 Участников: {len(participants)}/{game.min_participants}")
        lines.append(f"   📅 Жеребьёвка: {game.draw_date or 'не указана'}")
        lines.append("")
    
    bot.send_message(message.chat.id, "\n".join(lines))
    send_game_menu(message.chat.id)

def start_participants_lookup(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "participants_code", {})
    log_action("start_participants_lookup", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "👥 Введите код игры для просмотра участников:")

def start_join_game(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "join_code", {})
    log_action("start_join_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎮 Введите код игры для присоединения:")

def start_leave_game(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "leave_code", {})
    log_action("start_leave_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🚪 Введите код игры для выхода:")

def start_mix_game(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "mix_code", {})
    log_action("start_mix_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎉 Введите код игры для жеребьёвки:")

def show_my_recipient(message: types.Message) -> None:
    log_action("show_my_recipient", user_id=message.from_user.id)
    games = operations.get_participating_games(message.from_user.id)
    matches: List[str] = []
    
    for game in games:
        recipient = operations.get_match(game.id, message.from_user.id)
        if not recipient:
            continue
        
        profile = operations.get_profile(recipient)
        wishlist = operations.list_wishlist(recipient)
        
        lines = [
            f"🎅 <b>Вы — Тайный Санта!</b>",
            f"🎄 <b>Игра:</b> {game.title}",
            "",
            "👤 <b>Ваш получатель:</b>",
            f"📝 <b>ФИО:</b> {profile['full_name'] or 'не указано'}",
            f"ℹ️ <b>О себе:</b> {profile['bio'] or 'не указано'}"
        ]
        
        if wishlist:
            lines.extend(["", "🎁 <b>Вишлист получателя:</b>"])
            for i, item in enumerate(wishlist, 1):
                lines.append(f"{i}. {item['description']}")
        else:
            lines.extend(["", "📭 <b>Вишлист пуст</b>"])
        
        matches.append("\n".join(lines))
    
    if matches:
        for match_text in matches:
            bot.send_message(message.chat.id, match_text)
    else:
        bot.send_message(
            message.chat.id,
            "🎁 Пока нет назначенных получателей. Ждите жеребьёвки!",
        )

def start_ask_santa(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "ask_question", {})
    log_action("start_ask_santa", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "❓ Введите ваш вопрос для Тайного Санты:")

def join_game_by_code(user_id: int, chat_id: int, code: str) -> bool:
    game = operations.find_game_by_code(code)
    if not game:
        log_action("join_game_not_found", user_id=user_id, code=code)
        bot.send_message(chat_id, "❌ Игра не найдена. Проверьте код.")
        return False
    
    added = operations.add_participant(game.id, user_id)
    if added:
        bot.send_message(chat_id, f"🎉 Вы присоединились к игре \"<b>{game.title}</b>\"!")
    else:
        bot.send_message(chat_id, "ℹ️ Вы уже участвуете в этой игре.")
    
    log_action("join_game", user_id=user_id, code=code, joined=added)
    return True

def leave_game_by_code(user_id: int, chat_id: int, code: str) -> bool:
    game = operations.find_game_by_code(code)
    if not game:
        log_action("leave_game_not_found", user_id=user_id, code=code)
        bot.send_message(chat_id, "❌ Игра не найдена.")
        return False
    
    if operations.remove_participant(game.id, user_id):
        bot.send_message(chat_id, "🚪 Вы вышли из игры.")
        log_action("leave_game", user_id=user_id, code=code, removed=True)
    else:
        bot.send_message(chat_id, "❌ Не удалось выйти. Возможно, жеребьёвка уже проведена.")
        log_action("leave_game_failed", user_id=user_id, code=code)
    
    return True

def show_participants_by_code(message: types.Message, code: str) -> bool:
    game = operations.find_game_by_code(code)
    if not game:
        log_action("participants_not_found", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "❌ Игра не найдена.")
        return False
    
    if message.from_user.id not in operations.list_participants(game.id) and message.from_user.id != game.owner_id:
        log_action("participants_denied", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "❌ Вы не участвуете в этой игре.")
        return True
    
    participants = operations.list_participants(game.id)
    if not participants:
        log_action("participants_empty", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "👥 В игре пока нет участников.")
        return True
    
    log_action("participants_list", user_id=message.from_user.id, code=code, count=len(participants))
    
    lines = [
        f"👥 <b>Участники игры \"{game.title}\":</b>",
        f"🔑 Код: <code>{game.code}</code>",
        ""
    ]
    
    for i, uid in enumerate(participants, 1):
        profile = operations.get_profile(uid)
        display = profile["full_name"] or profile["username"] or f"ID{uid}"
        lines.append(f"{i}. {display}")
    
    lines.extend(["", f"Всего: {len(participants)} участников"])
    
    bot.send_message(message.chat.id, "\n".join(lines))
    return True

def mix_game_by_code(message: types.Message, code: str) -> bool:
    game = operations.find_game_by_code(code)
    if not game:
        log_action("mix_not_found", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "❌ Игра не найдена.")
        return False
    
    if not ensure_owner(message, game):
        return True
    
    participants = operations.list_participants(game.id)
    if len(participants) < game.min_participants or len(participants) < 3:
        log_action("mix_not_enough", user_id=message.from_user.id, code=code, count=len(participants))
        bot.send_message(
            message.chat.id, 
            f"❌ Недостаточно участников для жеребьёвки. Нужно: {game.min_participants}, есть: {len(participants)}"
        )
        return False
    
    shuffled = participants[:]
    random.shuffle(shuffled)
    recipients = shuffled[1:] + shuffled[:1]
    pairs = {santa: recipient for santa, recipient in zip(shuffled, recipients)}
    
    operations.store_matches(game.id, pairs)
    log_action("mix_success", user_id=message.from_user.id, code=code, count=len(participants))
    
    bot.send_message(message.chat.id, "🎉 Жеребьёвка проведена! Рассылаем результаты участникам...")
    notify_pairs(game, pairs)
    
    return True

def ask_santa_question(user_id: int, chat_id: int, question: str) -> bool:
    games = operations.get_participating_games(user_id)
    sent = 0
    
    for game in games:
        recipient = operations.get_match(game.id, user_id)
        if not recipient:
            continue
        
        profile = operations.get_profile(recipient)
        bot.send_message(
            recipient,
            f"❓ <b>Анонимный вопрос от вашего Санты (игра \"{game.title}\"):</b>\n\n{question}",
        )
        
        with operations.DB_LOCK:
            operations.DB.execute(
                "INSERT INTO anonymous_questions (game_id, santa_id, recipient_id, message, created_at) VALUES (?, ?, ?, ?, ?)",
                (game.id, user_id, recipient, question, operations.now_ts()),
            )
            operations.DB.commit()
        sent += 1
    
    log_action("ask_santa_result", user_id=user_id, sent=sent)
    
    if sent > 0:
        bot.send_message(chat_id, f"✅ Вопрос отправлен {sent} получателю(ям).")
    else:
        bot.send_message(chat_id, "❌ У вас пока нет получателей для вопросов.")
    
    return sent > 0

@bot.message_handler(commands=["create"])
def cmd_create_game(message: types.Message) -> None:
    start_create_game_flow(message)

@bot.message_handler(commands=["games"])
def cmd_status(message: types.Message) -> None:
    send_owner_status(message)

@bot.message_handler(commands=["participants"])
def cmd_participants(message: types.Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        start_participants_lookup(message)
        return
    operations.ensure_user(message.from_user.id, message.from_user.username)
    show_participants_by_code(message, parts[1])

@bot.message_handler(commands=["join"])
def cmd_join(message: types.Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        start_join_game(message)
        return
    operations.ensure_user(message.from_user.id, message.from_user.username)
    join_game_by_code(message.from_user.id, message.chat.id, parts[1])

@bot.message_handler(commands=["leave"])
def cmd_leave(message: types.Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        start_leave_game(message)
        return
    operations.ensure_user(message.from_user.id, message.from_user.username)
    leave_game_by_code(message.from_user.id, message.chat.id, parts[1])

@bot.message_handler(commands=["mix", "send"])
def cmd_mix(message: types.Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        start_mix_game(message)
        return
    mix_game_by_code(message, parts[1])

@bot.message_handler(commands=["recipient"])
def cmd_my_recipient(message: types.Message) -> None:
    show_my_recipient(message)

@bot.message_handler(commands=["ask"])
def cmd_ask(message: types.Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        log_action("command_ask_missing", user_id=message.from_user.id)
        bot.send_message(message.chat.id, "❌ Напишите вопрос: /ask Что бы вы хотели получить в подарок?")
        return
    
    question = parts[1].strip()
    ask_santa_question(message.from_user.id, message.chat.id, question)