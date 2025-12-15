from abc import ABC, abstractmethod

# ПАРАМЕТРЫ
BOB_SALARY = 80000
BOB_RENT = 30000
BOB_FOOD = 4000
BOB_TRANSPORT = 1500
BOB_CAT_FOOD = 2000
BOB_CAT_GROOMING = 3000
BOB_RENT_INFLATION = 0.05

ALICE_SALARY = 200000
ALICE_APARTMENT_PRICE = 10000000
ALICE_DOWN_PAYMENT = 2000000
ALICE_FOOD = 4000
ALICE_TRANSPORT = 1500
ALICE_MORTGAGE_RATE = 0.12
ALICE_MORTGAGE_YEARS = 20


class Person(ABC):
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary
        self.savings = 0
        self.months = 0
        self.total_income = 0
        self.total_expenses = 0

    def add_income(self):
        self.savings += self.salary
        self.total_income += self.salary

    def pay_expenses(self, amount):
        self.savings -= amount
        self.total_expenses += amount

    @abstractmethod
    def simulate_month(self):
        """Абстрактный метод для симуляции одного месяца жизни персонажа"""
        pass

    @abstractmethod
    def calculate_expenses(self):
        """Абстрактный метод для расчета текущих расходов персонажа"""
        pass


class Bob(Person):
    def __init__(self):
        super().__init__("Bob", BOB_SALARY)
        self.rent = BOB_RENT
        self.grooming_counter = 0

    def calculate_expenses(self):
        expenses = self.rent + BOB_FOOD + BOB_TRANSPORT + BOB_CAT_FOOD

        self.grooming_counter += 1
        if self.grooming_counter == 2:
            expenses += BOB_CAT_GROOMING
            self.grooming_counter = 0

        return expenses

    def apply_rent_inflation(self):
        if self.months % 12 == 0 and self.months > 0:
            self.rent = int(self.rent * (1 + BOB_RENT_INFLATION))

    def simulate_month(self):
        self.months += 1
        self.add_income()

        expenses = self.calculate_expenses()
        self.pay_expenses(expenses)
        self.apply_rent_inflation()

        return expenses


class Alice(Person):
    def __init__(self):
        super().__init__("Alice", ALICE_SALARY)
        self.loan = ALICE_APARTMENT_PRICE - ALICE_DOWN_PAYMENT
        self.remaining_loan = self.loan
        self.mortgage_paid = False

        monthly_rate = ALICE_MORTGAGE_RATE / 12
        months = ALICE_MORTGAGE_YEARS * 12
        self.mortgage_payment = int(
            (self.loan * monthly_rate * (1 + monthly_rate) ** months) /
            ((1 + monthly_rate) ** months - 1)
        )

    def calculate_expenses(self):
        """Реализация абстрактного метода для Alice"""
        living_expenses = ALICE_FOOD + ALICE_TRANSPORT
        mortgage_expense = self.mortgage_payment if not self.mortgage_paid and self.remaining_loan > 0 else 0
        return living_expenses + mortgage_expense

    def calculate_living_expenses(self):
        return ALICE_FOOD + ALICE_TRANSPORT

    def process_mortgage(self):
        if self.mortgage_paid or self.remaining_loan <= 0:
            return 0

        interest = self.remaining_loan * (ALICE_MORTGAGE_RATE / 12)
        principal = self.mortgage_payment - interest
        self.remaining_loan -= principal

        if self.remaining_loan < 0:
            self.savings -= self.remaining_loan
            self.remaining_loan = 0
            self.mortgage_paid = True

        return self.mortgage_payment

    def simulate_month(self):
        self.months += 1
        self.add_income()

        expenses = self.calculate_living_expenses()
        mortgage_payment = self.process_mortgage()
        expenses += mortgage_payment

        self.pay_expenses(expenses)
        return expenses


def format_number(num):
    """Форматирует число с разделителями тысяч и 2 знаками после запятой"""
    return f"{num:,.2f}".replace(",", " ").replace(".", ",")


def get_simulation_years():
    """Получает количество лет для симуляции от пользователя"""
    while True:
        try:
            years_input = input("Введите количество лет для симуляции: ").strip().lower()

            if years_input in ['inf', 'infinity', 'бесконечность']:
                print("Для бесконечной симуляции введите очень большое число, например 1000")
                continue

            years = float(years_input)

            if years <= 0:
                print("Введите число больше 0")
            elif years > 1000:
                print("Слишком большое значение. Введите число до 1000 лет")
            else:
                return years
        except ValueError:
            print("Ошибка! Введите число")


def calculate_alice_assets(alice):
    if alice.mortgage_paid:
        return alice.savings + ALICE_APARTMENT_PRICE
    else:
        apartment_equity = ALICE_APARTMENT_PRICE - alice.remaining_loan
        return alice.savings + apartment_equity


def run_simulation(bob, alice, years):
    """Запускает симуляцию на указанное количество лет"""
    try:
        months = int(years * 12)

        if months > 100000:
            print(f"Симуляция на {months:,} месяцев займет слишком много времени.")
            print("Пожалуйста, введите меньшее количество лет.")
            return False

        for month in range(months):
            bob.simulate_month()
            alice.simulate_month()

        return True

    except (OverflowError, MemoryError, ValueError) as e:
        print(f"Ошибка: невозможно выполнить симуляцию на {years} лет")
        print(f"Причина: {e}")
        return False


def print_results(years, bob, alice):
    alice_assets = calculate_alice_assets(alice)
    mortgage_status = ", ипотека выплачена" if alice.mortgage_paid else f", остаток долга = {format_number(alice.remaining_loan)} руб"

    results = [
        f"\nРезультаты за {format_number(years)} лет:",
        f"Bob: сбережения = {format_number(bob.savings)} руб, аренда = {format_number(bob.rent)} руб (начальная: {format_number(BOB_RENT)} руб)",
        f"Alice: сбережения = {format_number(alice.savings)} руб{mortgage_status}",
        f"Разница в сбережениях: {format_number(alice.savings - bob.savings)} руб",
        f"Общая стоимость активов: Bob = {format_number(bob.savings)} руб, Alice = {format_number(alice_assets)} руб"
    ]

    print("\n".join(results))


def main():
    print("Симуляция финансовых стратегий Боба и Алисы")
    print("=" * 50)

    years = get_simulation_years()

    bob = Bob()
    alice = Alice()

    if run_simulation(bob, alice, years):
        print_results(years, bob, alice)


if __name__ == "__main__":
    main()
