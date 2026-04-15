import os
import json

class Balances:
    def __init__(self):
        self.start_balance = 10000
        self.balance_file = "balances.json"


    def _load_balances(self):
        if os.path.exists(self.balance_file):
            with open(self.balance_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}


    def _save_balances(self, balances):
        with open(self.balance_file, 'w', encoding='utf-8') as f:
            json.dump(balances, f, ensure_ascii=False, indent=2)


    def get_balance(self, user_id):
        balances = self._load_balances()
        return balances.get(str(user_id), self.start_balance)


    def _update_balance(self, user_id, new_balance):
        balances = self._load_balances()
        balances[str(user_id)] = new_balance
        self._save_balances(balances)