# test_balance.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_handler import DatabaseHandler
from utils.transactions import TransactionManager


def test_balance():
    print("🔍 Тестирование системы баланса...")

    # Создаем экземпляры
    db = DatabaseHandler()
    transaction_manager = TransactionManager(db)

    # Тестовый пользователь
    test_user_id = 999999

    # 1. Создаем пользователя
    print(f"1. Создаем пользователя {test_user_id}...")
    user = db.create_user(test_user_id, "test_user", "Test", "User")
    initial_balance = db.get_user_balance(test_user_id)
    print(f"   Начальный баланс: {initial_balance}")

    # 2. Тестируем прямое обновление баланса
    print(f"2. Тестируем прямое обновление баланса...")
    success = db.update_user_balance(test_user_id, 100)
    new_balance = db.get_user_balance(test_user_id)
    print(f"   Обновление на +100: {'✅ Успех' if success else '❌ Ошибка'}")
    print(f"   Новый баланс: {new_balance} (ожидается: {initial_balance + 100})")

    # 3. Тестируем транзакцию с выигрышем
    print(f"3. Тестируем транзакцию с выигрышем...")
    current_balance = db.get_user_balance(test_user_id)
    print(f"   Баланс до транзакции: {current_balance}")

    transaction_success = transaction_manager.add_game_transaction(
        user_id=test_user_id,
        game_type='test_slots',
        bet=50,
        win=100,  # Чистый выигрыш +100
        result="Тестовый выигрыш"
    )

    new_balance = db.get_user_balance(test_user_id)
    print(f"   Транзакция: {'✅ Успех' if transaction_success else '❌ Ошибка'}")
    print(f"   Баланс после транзакции: {new_balance} (ожидается: {current_balance + 100})")

    # 4. Тестируем транзакцию с проигрышем
    print(f"4. Тестируем транзакцию с проигрышем...")
    current_balance = db.get_user_balance(test_user_id)
    print(f"   Баланс до транзакции: {current_balance}")

    transaction_success = transaction_manager.add_game_transaction(
        user_id=test_user_id,
        game_type='test_slots',
        bet=50,
        win=-50,  # Чистый проигрыш -50
        result="Тестовый проигрыш"
    )

    new_balance = db.get_user_balance(test_user_id)
    print(f"   Транзакция: {'✅ Успех' if transaction_success else '❌ Ошибка'}")
    print(f"   Баланс после транзакции: {new_balance} (ожидается: {current_balance - 50})")

    # 5. Проверяем данные в БД напрямую
    print(f"5. Проверяем данные в БД напрямую...")
    user_data = db.get_user(test_user_id)
    if user_data:
        print(f"   ✅ Данные пользователя из БД: ID={user_data.user_id}, Баланс={user_data.balance}")
    else:
        print(f"   ❌ Пользователь не найден")

    print("🎉 Тестирование завершено")


if __name__ == "__main__":
    test_balance()