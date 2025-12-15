import telebot
import sqlite3
import random
from datetime import datetime


BOT_TOKEN = 'INSERT_BOT_TOKEN_HERE'  # Замените на ваш токен
bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('santa_bot.db', check_same_thread=False)
cursor = conn.cursor()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        bio TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS wishlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_description TEXT,
        photo_id TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        game_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        draw_date TEXT,
        min_participants INTEGER,
        organizer_id INTEGER,
        code TEXT UNIQUE,
        FOREIGN KEY(organizer_id) REFERENCES users(user_id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_participants (
        game_id INTEGER,
        user_id INTEGER,
        PRIMARY KEY(game_id, user_id),
        FOREIGN KEY(game_id) REFERENCES games(game_id),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS distributions (
        game_id INTEGER,
        santa_user_id INTEGER,
        recipient_user_id INTEGER,
        PRIMARY KEY(game_id, santa_user_id),
        FOREIGN KEY(game_id) REFERENCES games(game_id),
        FOREIGN KEY(santa_user_id) REFERENCES users(user_id),
        FOREIGN KEY(recipient_user_id) REFERENCES users(user_id)
    )
''')
conn.commit()


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username


    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        bot.send_message(user_id, "Вы зарегистрированы! Используйте /profile для заполнения профиля.")
    else:
        bot.send_message(user_id, "Добро пожаловать обратно!")


@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Введите ваше ФИО:")
    bot.register_next_step_handler(message, set_full_name)


def set_full_name(message):
    user_id = message.from_user.id
    full_name = message.text
    cursor.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (full_name, user_id))
    conn.commit()
    bot.send_message(user_id, "Введите краткую биографию (хобби, интересы):")
    bot.register_next_step_handler(message, set_bio)


def set_bio(message):
    user_id = message.from_user.id
    bio = message.text
    cursor.execute("UPDATE users SET bio = ? WHERE user_id = ?", (bio, user_id))
    conn.commit()
    bot.send_message(user_id, "Профиль обновлен! Теперь вы можете создать вишлист с /wishlist.")


@bot.message_handler(commands=['wishlist'])
def wishlist(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Введите описание подарка (или 'done' для завершения):")
    bot.register_next_step_handler(message, add_wishlist_item)


def add_wishlist_item(message):
    user_id = message.from_user.id
    text = message.text
    if text.lower() == 'done':
        bot.send_message(user_id, "Вишлист сохранен!")
        return
    bot.send_message(user_id, "Отправьте фото для этого пункта (или напишите 'skip'):")
    bot.register_next_step_handler(message, lambda msg: process_photo(msg, text))


def process_photo(message, description):
    user_id = message.from_user.id
    photo_id = None
    if message.content_type == 'photo' and 'skip' not in message.text.lower():
        photo_id = message.photo[-1].file_id  # Получаем ID фото
    cursor.execute("INSERT INTO wishlists (user_id, item_description, photo_id) VALUES (?, ?, ?)",
                   (user_id, description, photo_id))
    conn.commit()
    bot.send_message(user_id, "Пункт добавлен! Добавьте следующий или напишите 'done'.")
    bot.register_next_step_handler(message, add_wishlist_item)


@bot.message_handler(commands=['create_game'])
def create_game(message):
    user_id = message.from_user.id  # Организатор
    bot.send_message(user_id, "Введите название игры:")
    bot.register_next_step_handler(message, set_game_name)


def set_game_name(message):
    game_name = message.text
    bot.send_message(message.chat.id, "Введите дату жеребьевки (формат: YYYY-MM-DD):")
    bot.register_next_step_handler(message, lambda msg: set_game_date(msg, game_name))


def set_game_date(message, game_name):
    draw_date = message.text
    bot.send_message(message.chat.id, "Введите минимальное количество участников (минимум 3):")
    bot.register_next_step_handler(message, lambda msg: create_game_final(msg, game_name, draw_date))


def create_game_final(message, game_name, draw_date):
    min_participants = int(message.text)
    if min_participants < 3:
        bot.send_message(message.chat.id, "Минимальное количество - 3. Попробуйте снова.")
        return
    code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))  # Уникальный код
    organizer_id = message.from_user.id
    cursor.execute("INSERT INTO games (name, draw_date, min_participants, organizer_id, code) VALUES (?, ?, ?, ?, ?)",
                   (game_name, draw_date, min_participants, organizer_id, code))
    conn.commit()
    game_id = cursor.lastrowid
    cursor.execute("INSERT INTO game_participants (game_id, user_id) VALUES (?, ?)", (game_id, organizer_id))
    conn.commit()
    bot.send_message(message.chat.id, f"Игра создана! Код приглашения: {code}")


@bot.message_handler(commands=['status'])
def status(message):
    user_id = message.from_user.id
    cursor.execute("SELECT game_id FROM game_participants WHERE user_id = ?", (user_id,))
    games = cursor.fetchall()
    for game in games:
        game_id = game[0]
        cursor.execute("SELECT name FROM games WHERE game_id = ?", (game_id,))
        game_name = cursor.fetchone()[0]
        cursor.execute(
            "SELECT users.username FROM game_participants JOIN users ON game_participants.user_id = users.user_id WHERE game_participants.game_id = ?",
            (game_id,))
        participants = cursor.fetchall()
        participant_list = [p[0] for p in participants]
        bot.send_message(user_id, f"Игра: {game_name}\nУчастники: {', '.join(participant_list)}")


@bot.message_handler(commands=['join'])
def join(message):
    try:
        code = message.text.split(' ', 1)[1]
        cursor.execute("SELECT game_id FROM games WHERE code = ?", (code,))
        game = cursor.fetchone()
        if game:
            game_id = game[0]
            user_id = message.from_user.id
            cursor.execute("INSERT INTO game_participants (game_id, user_id) VALUES (?, ?)", (game_id, user_id))
            conn.commit()
            bot.send_message(user_id, "Вы присоединились к игре!")
        else:
            bot.send_message(user_id, "Неверный код.")
    except:
        bot.send_message(user_id, "Используйте: /join <код>")


# Обработчик для выхода из игры
@bot.message_handler(commands=['leave'])
def leave(message):
    user_id = message.from_user.id
    cursor.execute(
        "DELETE FROM game_participants WHERE user_id = ? AND game_id IN (SELECT game_id FROM games WHERE draw_date > ?)",
        (user_id, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    bot.send_message(user_id, "Вы вышли из игры.")


# Жеребьевка
@bot.message_handler(commands=['mix'])
def mix(message):
    user_id = message.from_user.id
    cursor.execute("SELECT game_id FROM games WHERE organizer_id = ?", (user_id,))
    game = cursor.fetchone()
    if game:
        game_id = game[0]
        cursor.execute("SELECT user_id FROM game_participants WHERE game_id = ?", (game_id,))
        participants = [row[0] for row in cursor.fetchall()]
        if len(participants) < 3:
            bot.send_message(user_id, "Недостаточно участников.")
            return

        random.shuffle(participants)
        distribution = list(zip(participants, participants[1:] + [participants[0]]))
        for santa, recipient in distribution:
            if santa != recipient:
                cursor.execute("INSERT INTO distributions (game_id, santa_user_id, recipient_user_id) VALUES (?, ?, ?)",
                               (game_id, santa, recipient))
        conn.commit()

        for santa in participants:
            cursor.execute("SELECT recipient_user_id FROM distributions WHERE game_id = ? AND santa_user_id = ?",
                           (game_id, santa))
            recipient_id = cursor.fetchone()[0]
            cursor.execute("SELECT full_name, bio FROM users WHERE user_id = ?", (recipient_id,))
            recipient_info = cursor.fetchone()
            cursor.execute("SELECT item_description, photo_id FROM wishlists WHERE user_id = ?", (recipient_id,))
            wishlist = cursor.fetchall()
            wishlist_text = "\n".join(
                [f"- {item[0]}" + (f" (Фото: {item[1]})" if item[1] else "") for item in wishlist])
            message_text = f"Ваш получатель:\nФИО: {recipient_info[0]}\nБиография: {recipient_info[1]}\nВишлист:\n{wishlist_text}"
            bot.send_message(santa, message_text)
    bot.send_message(user_id, "Жеребьевка проведена!")


# Дополнительные функции
@bot.message_handler(commands=['my_recipient'])
def my_recipient(message):
    user_id = message.from_user.id
    cursor.execute("SELECT game_id, recipient_user_id FROM distributions WHERE santa_user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        game_id, recipient_id = result

        cursor.execute("SELECT full_name, bio FROM users WHERE user_id = ?", (recipient_id,))
        recipient_info = cursor.fetchone()
        cursor.execute("SELECT item_description, photo_id FROM wishlists WHERE user_id = ?", (recipient_id,))
        wishlist = cursor.fetchall()
        wishlist_text = "\n".join([f"- {item[0]}" + (f" (Фото: {item[1]})" if item[1] else "") for item in wishlist])
        message_text = f"Ваш получатель:\nФИО: {recipient_info[0]}\nБиография: {recipient_info[1]}\nВишлист:\n{wishlist_text}"
        bot.send_message(user_id, message_text)


@bot.message_handler(commands=['anonymous_question'])
def anonymous_question(message):
    user_id = message.from_user.id  # Santa
    cursor.execute("SELECT recipient_user_id FROM distributions WHERE santa_user_id = ?", (user_id,))
    recipient_id = cursor.fetchone()
    if recipient_id:
        recipient_id = recipient_id[0]
        bot.send_message(user_id, "Введите ваш анонимный вопрос:")
        bot.register_next_step_handler(message, lambda msg: send_anonymous_question(msg, recipient_id))


def send_anonymous_question(message, recipient_id):
    question = message.text
    bot.send_message(recipient_id, f"Анонимный вопрос от вашего Санты: {question}")


@bot.message_handler(commands=['help'])
def help(message):
    help_text = """
    Список команд:
    /start - Регистрация и запуск
    /profile - Создать/редактировать профиль
    /wishlist - Создать/редактировать вишлист
    /create_game - Создать новую игру
    /status - Просмотреть статус игры
    /join <код> - Присоединиться к игре
    /leave - Выйти из игры
    /mix - Запустить жеребьевку (для организатора)
    /my_recipient - Просмотреть информацию о получателе
    /anonymous_question - Отправить анонимный вопрос
    """
    bot.send_message(message.chat.id, help_text)




bot.polling()
