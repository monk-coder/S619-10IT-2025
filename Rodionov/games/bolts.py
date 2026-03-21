class Bolts:
    def __init__(self, bot):
        self.bot = bot

    def user_bolt(self, message, user_response):
        if user_response.lower() == "да":
            return random.randint(1, 6)
        elif user_response.lower() == "нет":
            self.bot.reply_to(message, "Действие отменено")
            return None
        else:
            self.bot.reply_to(message, "Введено неверное значение, попробуйте да/нет")
            return None

    def bot_bolt(self):
        return random.randint(1, 6)

    def result_game(self, user_bolt, bot_bolt):
        if user_bolt > bot_bolt:
            return "Вы выиграли!"
        elif user_bolt < bot_bolt:
            return "Вы проиграли!"
        else:
            return "Очки равны! Ничья!"

    def game_bolt(self, message, user_bolt, bot_bolt, result):
        if user_bolt is not None:
            self.bot.reply_to(message,
                              f"Ваш результат: {user_bolt}\nРезультат бота: {bot_bolt}\nРезультат: {result}")