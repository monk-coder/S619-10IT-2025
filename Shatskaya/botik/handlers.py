from bot_instance import bot
from states import user_states, create_game_states, games, user_games, user_data
from utils import generate_code
from db import BotDB
from telebot import types
import random

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        'Добро пожаловать в бот Тайного Санты!.\n' +
        'Список основных команд: /help.'
    )

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "Чтобы создать группу и получить код для вступления, напиши /create_game\n Чтобы вступить в группу по коду, напиши /join\n Чтобы обновить информацию о вас, напишите /info")

@bot.message_handler(commands=['join'])
def join(message):
    try:
        group_code = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "Использование: /join <код_группы>")
        return

    user_id = message.from_user.id

    if group_code not in games:
        bot.reply_to(message, "Группа не найдена. Проверьте, правильно ли вы ввели код.")
        return

    if games[game_code]['started']:
        bot.reply_to(message, "Код недействителен. Тайный Санта в этой группе уже начат.")
        return

    if user_id in [member['user_id'] for member in games[group_code]['participants']]:
        bot.reply_to(message, "Вы уже участвуете в этой группе.")
        return
    games[game_code]['members'].append({'user_id': user_id})

    if user_id not in user_data:
    user_data[user_id] = {}
user_data[user_id]['group'] = group_code

    bot.reply_to(message, "Вы присоединились к группе! Используйте команду /info, чтобы заполнить информацию о себе.")

@bot.message_handler(commands=['info'])
def info(message):
    user_states[message.from_user.id] = 'name'
    bot.reply_to(message, "Введите ваше имя (максимум 30 символов):")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'name')
def process_name(message):
    if len(message.text) > 30:
        bot.reply_to(message, "Слишком длинное имя.")
        return
    user_data[message.from_user.id]['name'] = message.text
    user_states[message.from_user.id] = 'bio'
    bot.reply_to(message, "Расскажите о себе (максимум 200 символов):")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'bio')
def process_bio(message):
    if len(message.text) > 200:
        bot.reply_to(message, "Слишком длинное описание.")
        return
    user_data[message.from_user.id]['bio'] = message.text
    user_states[message.from_user.id] = 'wishlist'
    bot.reply_to(message, "Напишите ваш вишлист (максимум 200 символов):")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'wishlist')
def process_wishlist(message):
    if len(message.text) > 200:
        bot.reply_to(message, "Много хочешь.")
        return
    user_data[message.from_user.id]['wishlist'] = message.text
    user_states[message.from_user.id] = 'photo'
    bot.reply_to(message, "Загрузите фото, на котором есть то, что вы хотите.")

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id) == 'photo')
def process_photo(message):
    file_id = message.photo[-1].file_id
    user_data[message.from_user.id]['photo'] = file_id
    user_id = message.from_user.id
    data = user_data[user_id]
    
    caption = f"Имя: {data['name']}\nО себе: {data['bio']}\nВишлист: {data['wishlist']}"
    bot.send_photo(message.chat.id, photo=file_id, caption=caption)
    bot.reply_to(message, "Инфо сохранено!")
    user_states[message.from_user.id] = None

@bot.message_handler(commands=['create_game'])
def create_game(message):
    create_game_states[message.from_user.id] = {'step': 'name'}
    bot.send_message(message.chat.id, "Введите название игры:")

@bot.message_handler(func=lambda message: 
    create_game_states.get(message.from_user.id, {}).get('step') == 'name')
def process_game_name(message):
    user_id = message.from_user.id
    create_game_states[user_id] = {
        'step': 'date',
        'name': message.text
    }
    bot.send_message(message.chat.id, "Введите дату начала ТС (например, 25.12.2025):")

@bot.message_handler(func=lambda message: 
    create_game_states.get(message.from_user.id, {}).get('step') == 'date')
def process_game_date(message):
    user_id = message.from_user.id
    create_game_states[user_id] = {
        'step': 'min_players', 
        'name': create_game_states[user_id]['name'],
        'date': message.text
    }
    bot.send_message(message.chat.id, "Введите минимальное количество участников (минимум 3):")

@bot.message_handler(func=lambda message: 
    create_game_states.get(message.from_user.id, {}).get('step') == 'min_players')
def process_min_players(message):
    try:
        min_players = int(message.text)
        if min_players < 3:
            bot.send_message(message.chat.id, "Минимум - 3.")
            return
    except ValueError:
        bot.send_message(message.chat.id, "Введите число участников цифрами.")
        return

    user_id = message.from_user.id
    game_code = generate_code()
    
    games[game_code] = {
        'name': create_game_states[user_id]['name'],
        'date': create_game_states[user_id]['date'],
        'min_players': min_players,
        'owner': user_id,
        'participants': [user_id],
        'started': False,
        'pairs': {}
    }

    if user_id not in user_games:
        user_games[user_id] = []
    user_games[user_id].append(game_code)
    
    del create_game_states[user_id]
    
    bot.send_message(
        message.chat.id,
        f"Игра создана!\n\n"
        f"Название: {games[game_code]['name']}\n"
        f"Дата: {games[game_code]['date']}\n"
        f"Минимум участников: {min_players}\n\n"
        f"Код для приглашения: '{game_code}'\n\n"
        f"Отправьте этот код участникам.",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['status'])
def game_status(message):
    user_id = message.from_user.id
    try:
        game_code = message.text.split()[1]
    except IndexError:
        if user_id not in user_games or not user_games[user_id]:
            bot.send_message(message.chat.id, "Вы не участвуете ни в одной игре")
            return
        
        game_list = "Ваши игры:\n\n" 
        for code in user_games[user_id]:
            game = games[code]
            status = "Жеребьевка еще не прошла" if not game['started'] else "Жеребьевка прошла"
            game_list += f"• {game['name']} (код: {code}) - {status}\n"
        
        bot.send_message(message.chat.id, game_list)
        return

    if game_code not in games:
        bot.send_message(message.chat.id, "Игра не найдена")
        return
    
    game = games[game_code]
    user_id = message.from_user.id
    
    if user_id not in game['participants']:
        bot.send_message(message.chat.id, "Вы не участвуете в этой игре")
        return
    
    participants_count = len(game['participants'])
    participants_list = "\n".join([f"• {user_data.get(pid, {}).get('name', f'Участник {pid}')}" 
                                  for pid in game['participants']])
    
    status_text = f"Игра: {game['name']}\n"
    status_text += f"Дата жеребьевки: {game['date']}\n"
    status_text += f"Участников: {participants_count}/{game['min_players']}\n\n"
    status_text += f"Участники:\n{participants_list}"
    
    if game['started']:
        status_text += "\n\nЖеребьевка завершена"
        if user_id in game['pairs']:
            receiver_id = game['pairs'][user_id]
            receiver_name = user_data.get(receiver_id, {}).get('name', 'Неизвестно')
            status_text += f"\nВы дарите: {receiver_name}"
    
    bot.send_message(message.chat.id, status_text)

@bot.message_handler(commands=['leave'])
def leave_game(message):
    try:
        game_code = message.text.split()[1]
    except IndexError:
        bot.send_message(message.chat.id, "Чтобы выйти из игры, напишите: /leave <код_игры>")
        return

    user_id = message.from_user.id

    if game_code not in games:
        bot.send_message(message.chat.id, "Игра не найдена")
        return
game = games[game_code]

    if game['started']:
        bot.send_message(message.chat.id, "Нельзя выйти после жеребьевки")
        return

    if user_id not in game['participants']:
        bot.send_message(message.chat.id, "Вы не участвуете в этой игре")
        return

    if user_id == game['owner']:
        bot.send_message(message.chat.id, "Владелец не может выйти из игры")
        return

    game['participants'].remove(user_id)
    user_games[user_id].remove(game_code)
    
    bot.send_message(message.chat.id, "Вы вышли из игры")

@bot.message_handler(commands=['mix'])
def start_mix(message):
    try:
        game_code = message.text.split()[1]
    except IndexError:
        bot.send_message(message.chat.id, "Использование: /mix <код_игры>")
        return

    user_id = message.from_user.id

    if game_code not in games:
        bot.send_message(message.chat.id, "Игра не найдена")
        return

    game = games[game_code]

    if game['owner'] != user_id:
        bot.send_message(message.chat.id, "Только организатор может запустить жеребьевку")
        return

    if game['started']:
        bot.send_message(message.chat.id, "Жеребьевка уже проведена")
        return

    if len(game['participants']) < game['min_players']:
        bot.send_message(
            message.chat.id,
            f"Недостаточно участников. Нужно минимум {game['min_players']}, а сейчас {len(game['participants'])}."
        )
        return

    shuffled = shuffle_participants(game['participants'])
    pairs = {}
    
    for i in range(len(game['participants'])):
        santa = game['participants'][i]
        receiver = shuffled[i]
        pairs[santa] = receiver

    game['pairs'] = pairs
    game['started'] = True

    successful_sends = 0
    for santa_id, receiver_id in pairs.items():
        if receiver_id in user_data:
            receiver_info = user_data[receiver_id]
            message_text = (
                f" Тайный Санта начался!\n\n"
                f"Ваш получатель: {receiver_info.get('name', 'Неизвестно')}\n"
                f"О себе: {receiver_info.get('bio', 'Не указано')}\n"
                f"Вишлист: {receiver_info.get('wishlist', 'Не указан')}"
            )
            
            try:
                if 'photo' in receiver_info:
                    bot.send_photo(santa_id, receiver_info['photo'], caption=message_text)
                else:
                    bot.send_message(santa_id, message_text)
                successful_sends += 1
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {santa_id}: {e}")

    bot.send_message(
        message.chat.id,
        f"Жеребьевка завершена!"
    )