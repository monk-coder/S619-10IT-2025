from telebot import types
from bot_instance import bot
from utils import log_action, set_step
from models import ensure_user, create_game, find_game_by_code, add_participant, remove_participant, list_participants, get_profile, get_games_for_owner, get_participating_games, get_match, store_matches, list_wishlist, Game
import random
from database import DB, DB_LOCK
from models import now_ts

def setup_game_handlers():
    @bot.message_handler(commands=["create_game"])
    def cmd_create_game(message: types.Message) -> None:
        start_create_game_flow(message)

    @bot.message_handler(commands=["status"])
    def cmd_status(message: types.Message) -> None:
        send_owner_status(message)

    @bot.message_handler(commands=["participants"])
    def cmd_participants(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2:
            start_participants_lookup(message)
            return
        ensure_user(message.from_user.id, message.from_user.username)
        show_participants_by_code(message, parts[1])

    @bot.message_handler(commands=["join"])
    def cmd_join(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2:
            start_join_game(message)
            return
        ensure_user(message.from_user.id, message.from_user.username)
        join_game_by_code(message.from_user.id, message.chat.id, parts[1])

    @bot.message_handler(commands=["leave"])
    def cmd_leave(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2:
            start_leave_game(message)
            return
        ensure_user(message.from_user.id, message.from_user.username)
        leave_game_by_code(message.from_user.id, message.chat.id, parts[1])

    @bot.message_handler(commands=["mix", "send"])
    def cmd_mix(message: types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2:
            start_mix_game(message)
            return
        mix_game_by_code(message, parts[1])

    @bot.message_handler(commands=["my_recipient"])
    def cmd_my_recipient(message: types.Message) -> None:
        show_my_recipient(message)

    @bot.message_handler(commands=["ask"])
    def cmd_ask(message: types.Message) -> None:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            log_action("command_ask_missing", user_id=message.from_user.id)
            bot.send_message(message.chat.id, "Напишите вопрос: /ask Что подарить?")
            return
        
        question = parts[1].strip()
        log_action("command_ask", user_id=message.from_user.id)
        games = get_participating_games(message.from_user.id)
        sent = 0
        
        for game in games:
            recipient = get_match(game.id, message.from_user.id)
            if not recipient:
                continue
            
            profile = get_profile(recipient)
            bot.send_message(
                recipient,
                f"<b>Анонимный вопрос от вашего Санты (игра {game.title}):</b>\n{question}",
            )
            
            with DB_LOCK:
                DB.execute(
                    "INSERT INTO anonymous_questions (game_id, santa_id, recipient_id, message, created_at) VALUES (?, ?, ?, ?, ?)",
                    (game.id, message.from_user.id, recipient, question, now_ts()),
                )
                DB.commit()
            sent += 1
        
        log_action("command_ask_result", user_id=message.from_user.id, sent=sent)
        bot.send_message(message.chat.id, "Вопрос отправлен." if sent else "У вас пока нет получателей.")

# Функции для игр
def start_create_game_flow(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "game_title", {})
    log_action("start_create_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎲 Введите название игры:")

def send_owner_status(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    log_action("view_owner_status", user_id=message.from_user.id)
    games = get_games_for_owner(message.from_user.id)
    if not games:
        bot.send_message(message.chat.id, "Пока нет созданных игр. Нажмите \"🎲 Создать игру\".")
        return
    lines = []
    for game in games:
        participants = list_participants(game.id)
        lines.append(
            f"<b>{game.title}</b> (код <code>{game.code}</code>) — {len(participants)} участника(ов), минимум {game.min_participants}"
        )
        if participants:
            names = []
            for uid in participants:
                profile = get_profile(uid)
                display = profile["full_name"] or profile["username"] or f"ID{uid}"
                names.append(display)
            lines.append("Участники: " + ", ".join(names))
        lines.append("")
    bot.send_message(message.chat.id, "\n".join(line for line in lines if line))

def start_participants_lookup(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "participants_code", {})
    log_action("start_participants_lookup", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "👥 Введите код игры, чтобы увидеть участников:")

def start_join_game(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "join_code", {})
    log_action("start_join_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎮 Введите код игры, чтобы присоединиться:")

def start_leave_game(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "leave_code", {})
    log_action("start_leave_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🚪 Введите код игры, чтобы выйти:")

def start_mix_game(message: types.Message) -> None:
    ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "mix_code", {})
    log_action("start_mix_game", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "🎉 Введите код игры для жеребьёвки:")

def show_my_recipient(message: types.Message) -> None:
    log_action("show_my_recipient", user_id=message.from_user.id)
    games = get_participating_games(message.from_user.id)
    matches = []
    for game in games:
        recipient = get_match(game.id, message.from_user.id)
        if not recipient:
            continue
        profile = get_profile(recipient)
        wishlist = list_wishlist(recipient)
        lines = [f"<b>{game.title}</b>"]
        lines.append(f"ФИО: {profile['full_name'] or 'не указано'}")
        lines.append(f"О себе: {profile['bio'] or 'не указано'}")
        if wishlist:
            lines.append("Вишлист:")
            for item in wishlist:
                lines.append(f"• {item['description']}")
        else:
            lines.append("Вишлист пуст.")
        matches.append("\n".join(lines))
    bot.send_message(
        message.chat.id,
        "\n\n".join(matches) if matches else "Пока нет назначенных получателей. Ждите жеребьёвки! 🎁",
    )

def join_game_by_code(user_id: int, chat_id: int, code: str) -> bool:
    game = find_game_by_code(code)
    if not game:
        log_action("join_game_not_found", user_id=user_id, code=code)
        bot.send_message(chat_id, "Игра не найдена. Попробуйте другой код ❗️")
        return False
    added = add_participant(game.id, user_id)
    bot.send_message(
        chat_id,
        "Вы уже участвуете в этой игре." if not added else f"🎉 Вы присоединились к игре <b>{game.title}</b>!",
    )
    log_action("join_game", user_id=user_id, code=code, joined=added)
    return True

def leave_game_by_code(user_id: int, chat_id: int, code: str) -> bool:
    game = find_game_by_code(code)
    if not game:
        log_action("leave_game_not_found", user_id=user_id, code=code)
        bot.send_message(chat_id, "Игра не найдена. Проверьте код.")
        return False
    if remove_participant(game.id, user_id):
        bot.send_message(chat_id, "🚪 Вы вышли из игры.")
        log_action("leave_game", user_id=user_id, code=code, removed=True)
    else:
        bot.send_message(chat_id, "Не удалось выйти. Возможно, жеребьёвка уже проведена.")
        log_action("leave_game_failed", user_id=user_id, code=code)
    return True

def show_participants_by_code(message: types.Message, code: str) -> bool:
    game = find_game_by_code(code)
    if not game:
        log_action("participants_not_found", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "Игра не найдена. Попробуйте снова.")
        return False
    if message.from_user.id not in list_participants(game.id) and message.from_user.id != game.owner_id:
        log_action("participants_denied", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "Вы не участвуете в этой игре.")
        return True
    participants = list_participants(game.id)
    if not participants:
        log_action("participants_empty", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "Пока нет участников.")
        return True
    log_action("participants_list", user_id=message.from_user.id, code=code, count=len(participants))
    lines = [f"<b>{game.title}</b>:"]
    for uid in participants:
        profile = get_profile(uid)
        display = profile["full_name"] or profile["username"] or f"ID{uid}"
        lines.append(display)
    bot.send_message(message.chat.id, "\n".join(lines))
    return True

def mix_game_by_code(message: types.Message, code: str) -> bool:
    game = find_game_by_code(code)
    if not game:
        log_action("mix_not_found", user_id=message.from_user.id, code=code)
        bot.send_message(message.chat.id, "Игра не найдена. Убедитесь в правильности кода.")
        return False
    if not ensure_owner(message, game):
        return True
    participants = list_participants(game.id)
    if len(participants) < game.min_participants or len(participants) < 3:
        log_action("mix_not_enough", user_id=message.from_user.id, code=code, count=len(participants))
        bot.send_message(message.chat.id, "Недостаточно участников для жеребьёвки.")
        return False
    shuffled = participants[:]
    random.shuffle(shuffled)
    recipients = shuffled[1:] + shuffled[:1]
    pairs = {santa: recipient for santa, recipient in zip(shuffled, recipients)}
    store_matches(game.id, pairs)
    log_action("mix_success", user_id=message.from_user.id, code=code, count=len(participants))
    bot.send_message(message.chat.id, "🎉 Жеребьёвка проведена! Рассылаем результаты участникам.")
    notify_pairs(game, pairs)
    return True

def ensure_owner(message: types.Message, game: Game) -> bool:
    if message.from_user.id != game.owner_id:
        log_action("ensure_owner_denied", user_id=message.from_user.id, code=game.code)
        bot.send_message(message.chat.id, "Только организатор может выполнить эту команду.")
        return False
    log_action("ensure_owner_ok", user_id=message.from_user.id, code=game.code)
    return True

def notify_pairs(game: Game, pairs: dict[int, int]) -> None:
    for santa_id, recipient_id in pairs.items():
        profile = get_profile(recipient_id)
        wishlist = list_wishlist(recipient_id)
        lines = [f"🎅 Вы Тайный Санта в игре <b>{game.title}</b>!", "🎁 Получатель:"]
        lines.append(f"ФИО: {profile['full_name'] or 'не указано'}")
        lines.append(f"О себе: {profile['bio'] or 'не указано'}")
        if wishlist:
            lines.append("🎉 Вишлист:")
            for item in wishlist:
                lines.append(f"• {item['description']}")
        else:
            lines.append("Вишлист пуст.")
        log_action("notify_pair", game_id=game.id, santa_id=santa_id, recipient_id=recipient_id)
        bot.send_message(santa_id, "\n".join(lines))
        for item in wishlist:
            if item["photo_file_id"]:
                bot.send_photo(santa_id, item["photo_file_id"], caption=item["description"])