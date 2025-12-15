import random

class Person:
    def __init__(self, name, salary, food_expenses, transport_expenses):
        self.name = name
        self.salary = float(salary)
        self.food_expenses = float(food_expenses)
        self.transport_expenses = float(transport_expenses)
        self.savings = 0.0
        self.month = 0
        self.year = 0
    
    def calculate_monthly_income(self):
        return self.salary
    
    def calculate_monthly_expenses(self):
        return self.food_expenses + self.transport_expenses
    
    def live_month(self):
        income = self.calculate_monthly_income()
        expenses = self.calculate_monthly_expenses()
        net_income = income - expenses
        
        self.savings += net_income
        self.month += 1
        
        if self.month % 12 == 0:
            self.year += 1
        
        return {
            'income': income,
            'expenses': expenses,
            'net_income': net_income,
            'savings': self.savings
        }


class Bob(Person):
    def __init__(self):
        super().__init__("Bob", 80000, 4000, 1500)
        self.rent = 30000.0
        self.cat_food = 2000.0
        self.cat_grooming = 3000.0
        self.grooming_counter = 0
    
    def calculate_monthly_expenses(self):
        expenses = super().calculate_monthly_expenses()
        expenses += self.rent
        expenses += self.cat_food
        
        self.grooming_counter += 1
        if self.grooming_counter % 2 == 0:
            expenses += self.cat_grooming
        
        if self.month > 0 and self.month % 12 == 0:
            self.rent = self.rent * 1.05
        
        return expenses


class Alice(Person):
    def __init__(self):
        super().__init__("Alice", 200000, 4000, 1500)
        self.apartment_price = 10000000.0
        self.mortgage_rate = 0.12
        self.mortgage_years = 20
        
        monthly_rate = self.mortgage_rate / 12
        total_months = self.mortgage_years * 12
        
        # Разбита сложная формула на читаемые части
        base = 1 + monthly_rate
        base_powered = base ** total_months
        numerator = self.apartment_price * monthly_rate * base_powered
        denominator = base_powered - 1
        self.mortgage_payment = numerator / denominator
        
        self.mortgage_balance = self.apartment_price
        self.coin_collection = set()  # Коллекция монет Алисы
        self.discarded_coins = 0      # Счетчик выброшенных монет
    
    def calculate_monthly_expenses(self):
        expenses = super().calculate_monthly_expenses()
        expenses += self.mortgage_payment
        
        interest = self.mortgage_balance * (self.mortgage_rate / 12)
        principal = self.mortgage_payment - interest
        self.mortgage_balance -= principal
        
        return expenses
    
    def get_apartment_equity(self):
        return max(0.0, self.apartment_price - self.mortgage_balance)
    
    def collect_coins(self, days_in_month=30):
        """Алиса коллекционирует монеты каждый день месяца"""
        max_denomination = 10000
        
        for _ in range(days_in_month):
            denomination = random.randint(1, max_denomination)
            
            if denomination in self.coin_collection:
                self.discarded_coins += 1
            else:
                self.coin_collection.add(denomination)
    
    def get_coin_stats(self):
        """Статистика коллекции монет Алисы"""
        return {
            'total_collected': len(self.coin_collection),
            'discarded': self.discarded_coins,
            'collection': sorted(self.coin_collection)
        }


def get_simulation_period():
    while True:
        try:
            years_input = input("Введите количество лет для симуляции (например, 3.5): ")
            years = float(years_input)
            if years <= 0:
                print("Количество лет должно быть положительным. Попробуйте снова.")
                continue
            
            # Разделяем на целые годы и месяцы
            total_months = round(years * 12)
            years_int = int(years)
            months = round((years - years_int) * 12)
            
            # Корректировка, если месяцы получились 12
            if months == 12:
                years_int += 1
                months = 0
            
            return years_int, months, total_months
            
        except ValueError:
            print("Пожалуйста, введите число (например, 3 или 3.5).")


def run_simulation():
    years_int, months, total_months = get_simulation_period()
    
    bob = Bob()
    alice = Alice()
    
    # Форматируем вывод в зависимости от введенных данных
    if years_int > 0 and months > 0:
        period_info = f"{years_int} лет и {months} месяцев"
    elif years_int > 0:
        period_info = f"{years_int} лет"
    else:
        period_info = f"{months} месяцев"
    
    print(f"""
Симуляция жизни Bob и Alice на {period_info}
Bob: зарплата {bob.salary:,.2f} руб/мес, аренда {bob.rent:,.2f} руб/мес
Alice: зарплата {alice.salary:,.2f} руб/мес, ипотека {alice.mortgage_payment:,.2f} руб/мес
""")
    
    for month in range(1, total_months + 1):
        bob.live_month()
        alice.live_month()
        alice.collect_coins()  # Алиса коллекционирует монеты каждый месяц
        
        if month % 12 == 0:
            year = month // 12
            bob_total = bob.savings
            alice_total = alice.savings + alice.get_apartment_equity()
            difference = alice_total - bob_total
            
            print(f"Год {year}: Bob {bob.savings:,.2f} руб | Alice {alice_total:,.2f} руб | Разница: {difference:,.2f} руб")
    
    # Финальные результаты симуляции жизни
    bob_total_wealth = bob.savings
    alice_total_wealth = alice.savings + alice.get_apartment_equity()
    wealth_difference = alice_total_wealth - bob_total_wealth
    
    print(f"""
ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ СИМУЛЯЦИИ ЖИЗНИ:

Bob:
  Сбережения: {bob.savings:,.2f} руб
  Текущая аренда: {bob.rent:,.2f} руб/мес

Alice:
  Сбережения: {alice.savings:,.2f} руб
  Доля в квартире: {alice.get_apartment_equity():,.2f} руб

ОБЩАЯ СТОИМОСТЬ АКТИВОВ:
  Bob: {bob_total_wealth:,.2f} руб
  Alice: {alice_total_wealth:,.2f} руб

Разница: {wealth_difference:,.2f} руб в пользу {'Alice' if wealth_difference > 0 else 'Bob'}
""")
    
    # Результаты коллекционирования монет
    coin_stats = alice.get_coin_stats()
    total_days = total_months * 30  # Предполагаем 30 дней в месяце
    
    # Показываем только первые 10 монет, если коллекция большая
    if coin_stats['total_collected'] > 10:
        first_ten = coin_stats['collection'][:10]
        collection_preview = f"Первые 10 номиналов: {first_ten}\n... и еще {coin_stats['total_collected'] - 10} монет"
    else:
        collection_preview = f"Номиналы собранных монет: {coin_stats['collection']}"
    
    print(f"""
КОЛЛЕКЦИЯ МОНЕТ АЛИСЫ:

Всего дней коллекционирования: {total_days}
Диапазон номиналов: 1-10000
Уникальных монет собрано: {coin_stats['total_collected']}
Монет выброшено (повторы): {coin_stats['discarded']}

{collection_preview}
""")


if __name__ == "__main__":
    run_simulation()