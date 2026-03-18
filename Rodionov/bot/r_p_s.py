import random


class r_p_s:
    def __init__(self, bot):
        self.bot = bot

    def get_bot_item(self):
        items = ["Камень", "Ножницы", "Бумага"]
        return random.choice(items)

    def determine_winner(self, user_item, bot_item):
        if user_item == bot_item:
            return "Ничья!"

        if (user_item == "Камень" and bot_item == "Ножницы") or \
           (user_item == "Ножницы" and bot_item == "Бумага") or \
           (user_item == "Бумага" and bot_item == "Камень"):
            return "Вы победили!"
        else:
            return "Вы проиграли!"

    def play(self, message, user_choice):
        if user_choice not in ["Камень", "Ножницы", "Бумага"]:
            self.bot.reply_to(message, "Некорректный ввод! Используйте: Камень, Ножницы или Бумага")
            return

        bot_choice = self.get_bot_item()
        result = self.determine_winner(user_choice, bot_choice)

        response = f"Бот выбрал: {bot_choice}\n"
        response += f"Вы выбрали: {user_choice}\n"
        response += f"Результат: {result}"

        self.bot.reply_to(message, response)