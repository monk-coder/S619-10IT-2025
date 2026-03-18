import telebot
from r_p_s import r_p_s

bot = telebot.TeleBot('8653855195:AAESBBa8LpQEWoY8FO4Q_0JDAlD8QaNifoQ')

user_names = {}


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "Привет! Для списка команд введите /help")
    print(f"Пользователь {message.from_user.first_name} запустил бота")


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
    Доступные команды:
    /start - Запустить бота
    /help - Показать список команд
    /name - Добавить свое имя
    /myinfo - Информация о тебе
    /r_p_s - Камень, ножницы, бумага
    """
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['name'])
def user_name(message):
    msg = bot.reply_to(message, "Привет! Введи свое имя:")
    bot.register_next_step_handler(msg, process_name)


def process_name(message):
    user_id = message.from_user.id
    user_name = message.text

    user_names[user_id] = user_name

    bot.reply_to(message, f"Отлично, {user_name}! Имя сохранено.")
    print(f"Пользователь {message.from_user.first_name} сохранил имя: {user_name}")


@bot.message_handler(commands=['myinfo'])
def myinfo(message):
    user_id = message.from_user.id
    if user_id in user_names:
        bot.reply_to(message, f"Твое сохраненное имя: {user_names[user_id]}")
    else:
        bot.reply_to(message, "Ты еще не сохранил имя. Используй /name")


@bot.message_handler(commands=['r_p_s'])
def start_rps(message):
    response = "Давай сыграем в КМН\n"
    response += "Выберите свой предмет(Камень, Ножницы, Бумага):"
    msg = bot.reply_to(message, response)
    bot.register_next_step_handler(msg, play_rps)

def play_rps(message):
    user_choice = message.text
    game = r_p_s(bot)
    game.play(message, user_choice)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True, interval=0)