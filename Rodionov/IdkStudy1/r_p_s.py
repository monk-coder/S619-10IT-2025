import random
import telebot

class r_p_s:
    def bot_item(message):
        bot_item = ["Камень", "Ножницы", "Бумага"]
        return random.choice(bot_item)

    def user_item(message):
         while True:
            bot.reply_to(message, "Выберите ваш предмет")
            user_item = message.text
            if user_item == "Камень" or "Ножницы" or "Бумага":
                return user_item
            else:
                bot.reply_to(message, "Введено неверное значение")
                break




    def game(message, bot_item):
        bot.reply_to(message, "Выберите предмет:")
            if message.text == "Камень" and bot_item == "Ножницы":
                game_process()
