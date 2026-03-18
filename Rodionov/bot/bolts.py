import random

class Bolts:
    def user_bolt(self, message):
       while True:
            bot.reply_to(message, f"Кинуть кубик?")
            if message.text == "Да" or "да":
                return random.randint(1, 6)
            elif message.text == "Нет" or "нет":
                bot.reply_to(message, f"Действие отменено")
                break
            else:
                bot.reply_to(message, f"Введено неверное значение, попробуйте да/нет")


    def bot_bolt(self):
        bot_bolt = random.randint(1, 6)
        return bot_bolt



