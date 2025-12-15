import json
import os
from config import DATA_FILE

def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {"transactions": [], "budgets": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"transactions": [], "budgets": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_transaction(data, transaction):
    data["transactions"].append(transaction)
    save_data(data)

def save_budget(data, user_id, category, limit):
    user_id = str(user_id)
    if user_id not in data["budgets"]:
        data["budgets"][user_id] = {}
    data["budgets"][user_id][category] = limit
    save_data(data)
