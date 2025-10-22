import json
import os


class Database:
    def __init__(self):
        self.users = {}
        self.load_data()

    def load_data(self):
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                self.users = json.load(f)

    def save_data(self):
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)

    def get_user(self, user_id):
        if str(user_id) not in self.users:
            from config import STARTING_BALANCE
            self.users[str(user_id)] = {
                'balance': STARTING_BALANCE,
                'games_played': 0,
                'wins': 0
            }
            self.save_data()
        return self.users[str(user_id)]

    def update_balance(self, user_id, amount):
        user = self.get_user(user_id)
        user['balance'] += amount
        user['games_played'] += 1
        if amount > 0:
            user['wins'] += 1
        self.save_data()
        return user['balance']


db = Database()