import telebot


bot = telebot.TeleBot('8653855195:AAESBBa8LpQEWoY8FO4Q_0JDAlD8QaNifoQ')

@bot.message_handler(comands=['start'])
def start_command(message):
    bot.reply_to(message, "Привет, для списка комманд введите /help")
    print(f"Пользователь {message.from_user.first_name} запустил бота")


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
    Доступные команды:
    /start - Запустить бота
    /help - Показать список комманд
    """
    bot.reply_to(message, help_text)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True, interval=30)
