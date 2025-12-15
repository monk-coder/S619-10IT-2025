# ПАРАМЕТРЫ
BOB_SALARY = 80_000
BOB_RENT = 30_000
BOB_FOOD = 4_000
BOB_TRANSPORT = 1_500
BOB_CAT_FOOD = 2_000
BOB_CAT_GROOMING = 3_000
BOB_RENT_INFLATION = 0.05

ALICE_SALARY = 200_000
ALICE_APARTMENT_PRICE = 10_000_000
ALICE_DOWN_PAYMENT = 2_000_000
ALICE_FOOD = 4_000
ALICE_TRANSPORT = 1_500
ALICE_MORTGAGE_RATE = 0.12
ALICE_MORTGAGE_YEARS = 20


class Person:
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


class Bob(Person):
    def __init__(self):
        super().__init__("Bob", BOB_SALARY)
        self.rent = BOB_RENT
        self.grooming_counter = 0

    def calculate_expenses(self):
        # Базовая аренда + расходы
        expenses = self.rent + BOB_FOOD + BOB_TRANSPORT + BOB_CAT_FOOD

        # Стрижка кота раз в 2 месяца
        self.grooming_counter += 1
        if self.grooming_counter == 2:
            expenses += BOB_CAT_GROOMING
            self.grooming_counter = 0

        return expenses

    def apply_rent_inflation(self):
        # Инфляция аренды раз в год
        if self.months % 12 == 0:
            self.rent = int(self.rent * (1 + BOB_RENT_INFLATION))

    def simulate_month(self):
        self.months += 1
        self.add_income()

        expenses = self.calculate_expenses()
        self.apply_rent_inflation()
        self.pay_expenses(expenses)

        return expenses


class Alice(Person):
    def __init__(self):
        super().__init__("Alice", ALICE_SALARY)
        self.loan = ALICE_APARTMENT_PRICE - ALICE_DOWN_PAYMENT
        self.remaining_loan = self.loan
        self.mortgage_paid = False

        # Расчет ежемесячного платежа по ипотеке
        monthly_rate = ALICE_MORTGAGE_RATE / 12
        months = ALICE_MORTGAGE_YEARS * 12
        self.mortgage_payment = int(
            (self.loan * monthly_rate * (1 + monthly_rate) ** months) /
            ((1 + monthly_rate) ** months - 1)
        )

    def calculate_living_expenses(self):
        return ALICE_FOOD + ALICE_TRANSPORT

    def process_mortgage(self):
        if self.mortgage_paid or self.remaining_loan <= 0:
            return 0

        interest = self.remaining_loan * (ALICE_MORTGAGE_RATE / 12)
        principal = self.mortgage_payment - interest
        self.remaining_loan -= principal

        if self.remaining_loan <= 0:
            self.savings += abs(self.remaining_loan)
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
    if isinstance(num, float):
        return f"{num:,.2f}"
    return f"{num:,}"


def get_simulation_years():
    """Получает количество лет для симуляции от пользователя"""
    while True:
        try:
            years = float(input("Введите количество лет для симуляции: "))
            if years > 0:
                return years
            print("Введите число больше 0")
        except ValueError:
            print("Ошибка! Введите число")


def calculate_alice_assets(alice):
    """Рассчитывает общую стоимость активов Алисы"""
    if alice.mortgage_paid:
        return alice.savings + ALICE_APARTMENT_PRICE
    else:
        return alice.savings + (ALICE_APARTMENT_PRICE - alice.remaining_loan)


def run_simulation(bob, alice, years):
    """Запускает симуляцию на указанное количество лет"""
    months = int(years * 12)

    for _ in range(months):
        bob.simulate_month()
        alice.simulate_month()


def print_results(years, bob, alice):
    """Выводит результаты симуляции"""
    alice_assets = calculate_alice_assets(alice)
    mortgage_status = ", ипотека выплачена" if alice.mortgage_paid else f", остаток долга = {format_number(alice.remaining_loan)} руб"

    results = [
        f"Результаты за {format_number(years)} лет:",
        f"Bob: сбережения = {format_number(bob.savings)} руб, аренда = {format_number(bob.rent)} руб (начальная: {format_number(BOB_RENT)} руб)",
        f"Alice: сбережения = {format_number(alice.savings)} руб{mortgage_status}",
        f"Разница в сбережениях: {format_number(alice.savings - bob.savings)} руб",
        f"Общая стоимость активов: Bob = {format_number(bob.savings)} руб, Alice = {format_number(alice_assets)} руб"
    ]

    print("\n" + "\n".join(results))


def main():
    years = get_simulation_years()

    bob = Bob()
    alice = Alice()

    run_simulation(bob, alice, years)
    print_results(years, bob, alice)


if __name__ == "__main__":
    main()   
