class Person:
    def __init__(self, name, salary, food_expenses, transport_expenses):
        self.name = name
        self.salary = salary
        self.food_expenses = food_expenses
        self.transport_expenses = transport_expenses
        self.savings = 0
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
        self.rent = 30000
        self.cat_food = 2000
        self.cat_grooming = 3000
        self.grooming_counter = 0

    def calculate_monthly_expenses(self):
        # Базовые расходы
        expenses = super().calculate_monthly_expenses()

        # Добавляем аренду
        expenses += self.rent

        # Добавляем еду для кота
        expenses += self.cat_food

        # Добавляем стрижку кота раз в 2 месяца
        self.grooming_counter += 1
        if self.grooming_counter % 2 == 0:
            expenses += self.cat_grooming

        # Индексация аренды раз в год
        if self.month > 0 and self.month % 12 == 0:
            self.rent = int(self.rent * 1.05)  # Округляем до целых

        return expenses


class Alice(Person):
    def __init__(self):
        super().__init__("Alice", 200000, 4000, 1500)
        self.apartment_price = 10000000
        self.mortgage_rate = 0.12
        self.mortgage_years = 20

        # Расчет аннуитетного платежа по ипотеке
        monthly_rate = self.mortgage_rate / 12
        total_months = self.mortgage_years * 12  # Переименовал переменную
        self.mortgage_payment = int((self.apartment_price * monthly_rate *
                                     (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1))

        # Текущая задолженность по ипотеке
        self.mortgage_balance = self.apartment_price

    def calculate_monthly_expenses(self):
        # Базовые расходы
        expenses = super().calculate_monthly_expenses()

        # Добавляем ипотечный платеж
        expenses += self.mortgage_payment

        # Уменьшаем задолженность по ипотеке
        interest = self.mortgage_balance * (self.mortgage_rate / 12)
        principal = self.mortgage_payment - interest
        self.mortgage_balance -= principal

        return expenses

    def get_apartment_equity(self):
        """Стоимость квартиры минус остаток по ипотеке"""
        return max(0, self.apartment_price - (self.apartment_price - self.mortgage_balance))


def run_simulation(years=5):
    bob = Bob()
    alice = Alice()

    print("=" * 80)
    print("СИМУЛЯЦИЯ ЖИЗНИ BOB И ALICE")
    print("=" * 80)
    print(f"\nНачальные условия:")
    print(f"Bob: зарплата {bob.salary:,} руб/мес, аренда {bob.rent:,} руб/мес")
    print(f"Alice: зарплата {alice.salary:,} руб/мес, ипотека {alice.mortgage_payment:,} руб/мес")
    print(f"Стоимость квартиры Alice: {alice.apartment_price:,} руб")
    print("\n" + "=" * 80)

    total_months = years * 12

    for month in range(1, total_months + 1):
        bob_data = bob.live_month()
        alice_data = alice.live_month()

        # Вывод годовых итогов
        if month % 12 == 0:
            year = month // 12
            print(f"\n--- ИТОГИ ЗА {year}-Й ГОД ---")
            print(f"Bob:")
            print(f"  Сбережения: {bob.savings:,} руб")
            print(f"  Ежемесячная аренда: {bob.rent:,} руб")

            print(f"Alice:")
            print(f"  Сбережения: {alice.savings:,} руб")
            print(f"  Остаток по ипотеке: {alice.mortgage_balance:,.0f} руб")

            # Сравнение финансового положения
            bob_total = bob.savings
            alice_total = alice.savings + alice.get_apartment_equity()
            difference = alice_total - bob_total
            print(f"Общая разница в активах: {difference:,.0f} руб в пользу {'Alice' if difference > 0 else 'Bob'}")

        # Финальные результаты
    print("\n" + "=" * 80)
    print("ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ СИМУЛЯЦИИ")
    print("=" * 80)

    print(f"\nПосле {years} лет:")

    print(f"\nBob:")
    print(f"  Итоговые сбережения: {bob.savings:,} руб")
    print(f"  Ежемесячная аренда: {bob.rent:,} руб")

    print(f"\nAlice:")
    print(f"  Итоговые сбережения: {alice.savings:,} руб")
    print(f"  Остаток по ипотеке: {alice.mortgage_balance:,.0f} руб")
    print(f"  Доля в квартире: {alice.get_apartment_equity():,.0f} руб")

    # Общая стоимость активов
    bob_total_wealth = bob.savings
    alice_total_wealth = alice.savings + alice.get_apartment_equity()

    print(f"\nОБЩАЯ СТОИМОСТЬ АКТИВОВ:")
    print(f"  Bob: {bob_total_wealth:,} руб (только сбережения)")
    print(f"  Alice: {alice_total_wealth:,.0f} руб (сбережения + доля в квартире)")

    wealth_difference = alice_total_wealth - bob_total_wealth
    print(f"Разница: {wealth_difference:,.0f} руб в пользу {'Alice' if wealth_difference > 0 else 'Bob'}")


if __name__ == "__main__":
    # Запуск симуляции на 5 лет
    run_simulation(5)