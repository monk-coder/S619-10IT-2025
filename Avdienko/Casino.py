import random
import requests
import time


class SimpleCasinoBot:
    def __init__(self, token):
        self.token = token
        self.url = f"https://api.telegram.org/bot{token}/"

    def send_message(self, chat_id, text):
        url = self.url + "sendMessage"
        data = {"chat_id": chat_id, "text": text}
        requests.post(url, data=data)

    def get_updates(self):
        url = self.url + "getUpdates"
        response = requests.get(url)
        return response.json()

    def run(self):
        print("🎰 Простой казино бот запущен!")
        last_update_id = 0

        while True:
            updates = self.get_updates()

            if "result" in updates:
                for update in updates["result"]:
                    if update["update_id"] > last_update_id:
                        last_update_id = update["update_id"]

                        if "message" in update:
                            chat_id = update["message"]["chat"]["id"]
                            text = update["message"].get("text", "")

                            if text == "/start":
                                self.send_message(chat_id,
                                                  "🎰 Добро пожаловать в казино! 🎰\n\nИгры:\n• /slots - игровые автоматы\n• /dice - кости\n• /balance - баланс")

                            elif text == "/slots":
                                symbols = ["🍒", "🍋", "🍊", "💎"]
                                reels = [random.choice(symbols) for _ in range(3)]
                                result = f"🎰 | {reels[0]} | {reels[1]} | {reels[2]} |"
                                self.send_message(chat_id, result)

                            elif text == "/dice":
                                dice1, dice2 = random.randint(1, 6), random.randint(1, 6)
                                result = f"🎲 Кости: {dice1} и {dice2} = {dice1 + dice2}"
                                self.send_message(chat_id, result)

                            elif text == "/balance":
                                self.send_message(chat_id, "💰 Баланс: 1000 монет")

            time.sleep(1)


# Запуск
if __name__ == "__main__":
    token = "8397370495:AAFsNypdtSFP4AOmahzyebk8TPZZvciaqN8"
    bot = SimpleCasinoBot(token)
    bot.run()