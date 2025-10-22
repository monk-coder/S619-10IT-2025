import random
import sqlite3
import time
from datetime import datetime, timedelta
import os


class RealLifeGame:
    def __init__(self):
        self.init_db()
        self.players = {}
        self.current_player = None

    def init_db(self):
        conn = sqlite3.connect('real_life_game.db')
        cursor = conn.cursor()

        # Игроки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                balance INTEGER DEFAULT 1000,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                last_work TEXT,
                last_crime TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Имущество
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                type TEXT,
                name TEXT,
                price INTEGER,
                income INTEGER,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players (id)
            )
        ''')

        # Биткоины
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bitcoin (
                player_id INTEGER PRIMARY KEY,
                amount REAL DEFAULT 0,
                price REAL DEFAULT 50000,
                FOREIGN KEY (player_id) REFERENCES players (id)
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")

    def register_player(self, name):
        conn = sqlite3.connect('real_life_game.db')
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO players (name) VALUES (?)', (name,))
            player_id = cursor.lastrowid
            cursor.execute('INSERT INTO bitcoin (player_id) VALUES (?)', (player_id,))
            conn.commit()

            player = {
                'id': player_id,
                'name': name,
                'balance': 1000,
                'level': 1,
                'experience': 0,
                'energy': 100,
                'last_work': None,
                'last_crime': None
            }

            self.current_player = player
            print(f"🎮 Игрок {name} зарегистрирован!")
            return player

        except sqlite3.IntegrityError:
            print("❌ Игрок с таким именем уже существует!")
            return None
        finally:
            conn.close()

    def login(self, name):
        conn = sqlite3.connect('real_life_game.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT p.*, b.amount, b.price 
            FROM players p 
            LEFT JOIN bitcoin b ON p.id = b.player_id 
            WHERE p.name = ?
        ''', (name,))

        player_data = cursor.fetchone()
        conn.close()

        if player_data:
            player = {
                'id': player_data[0],
                'name': player_data[1],
                'balance': player_data[2],
                'level': player_data[3],
                'experience': player_data[4],
                'energy': player_data[5],
                'last_work': player_data[6],
                'last_crime': player_data[7],
                'bitcoin_amount': player_data[9],
                'bitcoin_price': player_data[10]
            }
            self.current_player = player
            print(f"👋 Добро пожаловать, {name}!")
            return player
        else:
            print("❌ Игрок не найден!")
            return None

    def save_player(self):
        if not self.current_player:
            return

        conn = sqlite3.connect('real_life_game.db')
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE players SET 
            balance = ?, level = ?, experience = ?, energy = ?, 
            last_work = ?, last_crime = ?
            WHERE id = ?
        ''', (
            self.current_player['balance'],
            self.current_player['level'],
            self.current_player['experience'],
            self.current_player['energy'],
            self.current_player['last_work'],
            self.current_player['last_crime'],
            self.current_player['id']
        ))

        cursor.execute('UPDATE bitcoin SET amount = ?, price = ? WHERE player_id = ?', (
            self.current_player.get('bitcoin_amount', 0),
            self.current_player.get('bitcoin_price', 50000),
            self.current_player['id']
        ))

        conn.commit()
        conn.close()

    def add_experience(self, exp):
        self.current_player['experience'] += exp
        exp_needed = self.current_player['level'] * 100

        if self.current_player['experience'] >= exp_needed:
            self.current_player['level'] += 1
            self.current_player['experience'] = 0
            print(f"🎉 Уровень повышен! Теперь уровень {self.current_player['level']}")
            return True
        return False

    def work(self):
        jobs = [
            {"name": "💼 Офисный работник", "min": 50, "max": 150, "energy": 10, "exp": 10},
            {"name": "🚚 Водитель грузовика", "min": 80, "max": 200, "energy": 15, "exp": 15},
            {"name": "👨‍💻 Программист", "min": 150, "max": 400, "energy": 20, "exp": 25}
        ]

        print("\n💼 ВЫБЕРИ РАБОТУ:")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['name']} - ${job['min']}-${job['max']} (Энергия: {job['energy']}⚡)")

        try:
            choice = int(input("Выбери работу (1-3): ")) - 1
            if choice < 0 or choice >= len(jobs):
                print("❌ Неверный выбор!")
                return
        except ValueError:
            print("❌ Введи число!")
            return

        job = jobs[choice]

        if self.current_player['energy'] < job['energy']:
            print("❌ Недостаточно энергии!")
            return

        # Кулдаун 30 секунд
        if self.current_player['last_work']:
            last_work = datetime.fromisoformat(self.current_player['last_work'])
            if datetime.now() - last_work < timedelta(seconds=30):
                print("⏰ Подожди 30 секунд перед следующей работой!")
                return

        salary = random.randint(job['min'], job['max'])
        self.current_player['balance'] += salary
        self.current_player['energy'] -= job['energy']
        self.current_player['last_work'] = datetime.now().isoformat()

        level_up = self.add_experience(job['exp'])

        print(f"\n✅ {job['name']} выполнена!")
        print(f"💵 Зарплата: ${salary}")
        print(f"💰 Баланс: ${self.current_player['balance']}")
        print(f"⚡ Энергия: {self.current_player['energy']}/100")
        print(f"⭐ Опыт: +{job['exp']}")

        if level_up:
            print(f"🎉 Новый уровень: {self.current_player['level']}!")

        self.save_player()

    def crime(self):
        crimes = [
            {"name": "🛒 Украсть продукты", "success_rate": 80, "min": 20, "max": 100, "penalty": 50, "energy": 5,
             "exp": 5},
            {"name": "🏪 Ограбить магазин", "success_rate": 60, "min": 100, "max": 500, "penalty": 200, "energy": 15,
             "exp": 15},
            {"name": "💰 Ограбить банк", "success_rate": 30, "min": 1000, "max": 5000, "penalty": 1000, "energy": 40,
             "exp": 50}
        ]

        print("\n🕵️ ВЫБЕРИ ПРЕСТУПЛЕНИЕ:")
        for i, crime in enumerate(crimes, 1):
            print(f"{i}. {crime['name']}")
            print(f"   Добыча: ${crime['min']}-${crime['max']}")
            print(f"   Шанс: {crime['success_rate']}% | Штраф: ${crime['penalty']}")
            print(f"   Энергия: {crime['energy']}⚡")
            print()

        try:
            choice = int(input("Выбери преступление (1-3): ")) - 1
            if choice < 0 or choice >= len(crimes):
                print("❌ Неверный выбор!")
                return
        except ValueError:
            print("❌ Введи число!")
            return

        crime = crimes[choice]

        if self.current_player['energy'] < crime['energy']:
            print("❌ Недостаточно энергии!")
            return

        # Кулдаун 60 секунд
        if self.current_player['last_crime']:
            last_crime = datetime.fromisoformat(self.current_player['last_crime'])
            if datetime.now() - last_crime < timedelta(seconds=60):
                print("⏰ Подожди 60 секунд перед следующим преступлением!")
                return

        success = random.randint(1, 100) <= crime['success_rate']
        self.current_player['energy'] -= crime['energy']
        self.current_player['last_crime'] = datetime.now().isoformat()

        print(f"\nПопытка {crime['name']}...")
        time.sleep(2)

        if success:
            loot = random.randint(crime['min'], crime['max'])
            self.current_player['balance'] += loot
            print("✅ ПРЕСТУПЛЕНИЕ УСПЕШНО!")
            print(f"💰 Добыча: ${loot}")
            self.add_experience(crime['exp'])
        else:
            penalty = crime['penalty']
            self.current_player['balance'] = max(0, self.current_player['balance'] - penalty)
            print("❌ ПРОВАЛ!")
            print(f"💸 Штраф: ${penalty}")
            self.add_experience(crime['exp'] // 2)

        print(f"💵 Баланс: ${self.current_player['balance']}")
        print(f"⚡ Энергия: {self.current_player['energy']}/100")

        self.save_player()

    def casino(self):
        print("\n🎰 ДОБРО ПОЖАЛОВАТЬ В КАЗИНО!")
        print("Твой баланс: ${:,}".format(self.current_player['balance']))

        try:
            bet = int(input("Введи сумму ставки: "))
            if bet <= 0:
                print("❌ Ставка должна быть больше 0!")
                return
            if bet > self.current_player['balance']:
                print("❌ Недостаточно средств!")
                return
        except ValueError:
            print("❌ Введи число!")
            return

        games = [
            {"name": "🎰 Автоматы", "multiplier": 2, "chance": 45},
            {"name": "🎲 Кости", "multiplier": 3, "chance": 33},
            {"name": "🃏 Блэкджек", "multiplier": 2.5, "chance": 40}
        ]

        print("\nВыбери игру:")
        for i, game in enumerate(games, 1):
            print(f"{i}. {game['name']} - x{game['multiplier']} (Шанс: {game['chance']}%)")

        try:
            choice = int(input("Выбор (1-3): ")) - 1
            if choice < 0 or choice >= len(games):
                print("❌ Неверный выбор!")
                return
        except ValueError:
            print("❌ Введи число!")
            return

        game = games[choice]
        win = random.randint(1, 100) <= game['chance']

        print(f"\nИграем в {game['name']}...")
        time.sleep(2)

        if win:
            win_amount = bet * game['multiplier']
            self.current_player['balance'] += win_amount
            print("🎉 ПОБЕДА!")
            print(f"💰 Выигрыш: ${win_amount:,}")
        else:
            self.current_player['balance'] -= bet
            print("💸 ПРОИГРЫШ")
            print(f"😥 Потеряно: ${bet:,}")

        print(f"💎 Баланс: ${self.current_player['balance']:,}")
        self.add_experience(bet // 10)
        self.save_player()

    def shop(self):
        properties = [
            {"type": "car", "name": "🚗 Toyota", "price": 5000, "income": 0},
            {"type": "car", "name": "🚙 Mercedes", "price": 50000, "income": 100},
            {"type": "house", "name": "🏠 Квартира", "price": 100000, "income": 200},
            {"type": "business", "name": "🏢 Бизнес", "price": 200000, "income": 500}
        ]

        # Получаем имущество игрока
        conn = sqlite3.connect('real_life_game.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM properties WHERE player_id = ?', (self.current_player['id'],))
        owned_properties = [row[0] for row in cursor.fetchall()]
        conn.close()

        print("\n🛒 МАГАЗИН")
        print(f"💰 Твой баланс: ${self.current_player['balance']:,}")

        print("\n🏠 Твое имущество:")
        if owned_properties:
            for prop in owned_properties:
                print(f"• {prop}")
        else:
            print("Пока ничего...")

        print("\n🛍️ Доступно для покупки:")
        available = []
        for i, prop in enumerate(properties, 1):
            if prop['name'] not in owned_properties:
                available.append((i, prop))
                print(f"{i}. {prop['name']} - ${prop['price']:,}")
                if prop['income'] > 0:
                    print(f"   💸 Доход: ${prop['income']}/день")
                print()

        if not available:
            print("Ты уже купил всё доступное имущество!")
            return

        try:
            choice = int(input("Выбери номер для покупки (0 - отмена): "))
            if choice == 0:
                return

            selected = None
            for num, prop in available:
                if num == choice:
                    selected = prop
                    break

            if not selected:
                print("❌ Неверный выбор!")
                return

        except ValueError:
            print("❌ Введи число!")
            return

        if self.current_player['balance'] < selected['price']:
            print("❌ Недостаточно средств!")
            return

        # Покупаем
        self.current_player['balance'] -= selected['price']

        conn = sqlite3.connect('real_life_game.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO properties (player_id, type, name, price, income)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.current_player['id'], selected['type'], selected['name'], selected['price'], selected['income']))
        conn.commit()
        conn.close()

        print(f"\n✅ Куплено: {selected['name']}")
        print(f"💵 Потрачено: ${selected['price']:,}")
        print(f"💰 Остаток: ${self.current_player['balance']:,}")

        if selected['income'] > 0:
            print(f"💸 Пассивный доход: ${selected['income']}/день")

        self.add_experience(selected['price'] // 100)
        self.save_player()

    def bitcoin(self):
        if 'bitcoin_amount' not in self.current_player:
            self.current_player['bitcoin_amount'] = 0
            self.current_player['bitcoin_price'] = 50000

        print("\n₿ БИТКОИН")
        print(f"📊 Текущий курс: ${self.current_player['bitcoin_price']:,}")
        print(f"💼 Твои биткоины: {self.current_player['bitcoin_amount']:.6f}")

        btc_value = self.current_player['bitcoin_amount'] * self.current_player['bitcoin_price']
        print(f"💰 Стоимость: ${btc_value:,.2f}")
        print(f"💵 Баланс: ${self.current_player['balance']:,}")

        print("\n1. Купить биткоин")
        print("2. Продать биткоин")
        print("3. Обновить курс")
        print("0. Назад")

        try:
            choice = int(input("Выбери действие: "))
        except ValueError:
            print("❌ Введи число!")
            return

        if choice == 1:  # Купить
            try:
                amount = float(input("Сумма в долларах для покупки: "))
                if amount <= 0:
                    print("❌ Сумма должна быть положительной!")
                    return
                if amount > self.current_player['balance']:
                    print("❌ Недостаточно средств!")
                    return

                btc_amount = amount / self.current_player['bitcoin_price']
                self.current_player['bitcoin_amount'] += btc_amount
                self.current_player['balance'] -= amount

                print(f"✅ Куплено {btc_amount:.6f} BTC за ${amount:,.2f}")

            except ValueError:
                print("❌ Введи число!")

        elif choice == 2:  # Продать
            try:
                btc_amount = float(input("Количество биткоинов для продажи: "))
                if btc_amount <= 0:
                    print("❌ Количество должно быть положительным!")
                    return
                if btc_amount > self.current_player['bitcoin_amount']:
                    print("❌ Недостаточно биткоинов!")
                    return

                usd_amount = btc_amount * self.current_player['bitcoin_price']
                self.current_player['bitcoin_amount'] -= btc_amount
                self.current_player['balance'] += usd_amount

                print(f"✅ Продано {btc_amount:.6f} BTC за ${usd_amount:,.2f}")

            except ValueError:
                print("❌ Введи число!")

        elif choice == 3:  # Обновить курс
            change = random.uniform(-0.2, 0.2)  # ±20%
            old_price = self.current_player['bitcoin_price']
            self.current_player['bitcoin_price'] = max(1000, old_price * (1 + change))

            print(f"📊 Курс обновлен: {change:+.1%}")
            print(f"💰 Новый курс: ${self.current_player['bitcoin_price']:,.2f}")

        self.save_player()

    def profile(self):
        if not self.current_player:
            print("❌ Сначала войди в игру!")
            return

        # Получаем имущество
        conn = sqlite3.connect('real_life_game.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, income FROM properties WHERE player_id = ?', (self.current_player['id'],))
        properties = cursor.fetchall()
        conn.close()

        total_income = sum(prop[1] for prop in properties)
        btc_value = self.current_player.get('bitcoin_amount', 0) * self.current_player.get('bitcoin_price', 50000)
        net_worth = self.current_player['balance'] + btc_value + sum(prop[1] * 100 for prop in properties)

        print(f"\n📊 ПРОФИЛЬ ИГРОКА {self.current_player['name']}")
        print("=" * 40)
        print(f"💰 Баланс: ${self.current_player['balance']:,}")
        print(f"₿ Биткоины: {self.current_player.get('bitcoin_amount', 0):.6f} (${btc_value:,.2f})")
        print(f"💵 Общий капитал: ${net_worth:,.2f}")
        print(f"⭐ Уровень: {self.current_player['level']}")
        print(f"📊 Опыт: {self.current_player['experience']}/{self.current_player['level'] * 100}")
        print(f"⚡ Энергия: {self.current_player['energy']}/100")

        print(f"\n🏠 Имущество ({len(properties)}):")
        for prop in properties:
            print(f"• {prop[0]}", end="")
            if prop[1] > 0:
                print(f" (+${prop[1]}/день)", end="")
            print()

        print(f"💸 Пассивный доход: ${total_income}/день")

    def main_menu(self):
        while True:
            if not self.current_player:
                print("\n" + "=" * 50)
                print("🎮 REAL LIFE GAME")
                print("=" * 50)
                print("1. Регистрация")
                print("2. Вход")
                print("3. Выход")

                try:
                    choice = int(input("Выбери действие: "))
                except ValueError:
                    print("❌ Введи число!")
                    continue

                if choice == 1:
                    name = input("Введи имя игрока: ").strip()
                    if name:
                        self.register_player(name)
                    else:
                        print("❌ Имя не может быть пустым!")
                elif choice == 2:
                    name = input("Введи имя игрока: ").strip()
                    if name:
                        self.login(name)
                    else:
                        print("❌ Введи имя!")
                elif choice == 3:
                    print("👋 До свидания!")
                    break
                else:
                    print("❌ Неверный выбор!")
            else:
                print(f"\n🎮 REAL LIFE GAME - {self.current_player['name']}")
                print("=" * 40)
                print("1. 💼 Работа")
                print("2. 🕵️ Преступления")
                print("3. 🎰 Казино")
                print("4. 🏠 Магазин")
                print("5. ₿ Биткоин")
                print("6. 📊 Профиль")
                print("7. 🔄 Восстановить энергию")
                print("8. 🚪 Выйти из аккаунта")
                print("9. ❌ Выйти из игры")

                try:
                    choice = int(input("Выбери действие: "))
                except ValueError:
                    print("❌ Введи число!")
                    continue

                if choice == 1:
                    self.work()
                elif choice == 2:
                    self.crime()
                elif choice == 3:
                    self.casino()
                elif choice == 4:
                    self.shop()
                elif choice == 5:
                    self.bitcoin()
                elif choice == 6:
                    self.profile()
                elif choice == 7:
                    cost = 50 * (100 - self.current_player['energy'])
                    if self.current_player['balance'] >= cost:
                        self.current_player['energy'] = 100
                        self.current_player['balance'] -= cost
                        print(f"✅ Энергия восстановлена! Потрачено ${cost}")
                        self.save_player()
                    else:
                        print("❌ Недостаточно средств!")
                elif choice == 8:
                    self.current_player = None
                    print("👋 Вышел из аккаунта!")
                elif choice == 9:
                    print("👋 До свидания!")
                    break
                else:
                    print("❌ Неверный выбор!")


# Запуск игры
if __name__ == "__main__":
    game = RealLifeGame()
    game.main_menu()