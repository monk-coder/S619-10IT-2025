import math
import random

# ===================
# Константы Боба
# ===================
BOB_START_BALANCE = 100_000
BOB_SALARY = 80_000
BOB_RENT_START = 30_000
BOB_RENT_INDEXATION = 0.05  # индексация стоимости квартиры в год
BOB_FOOD = 4_000
BOB_TRANSPORT = 1_500
CAT_FOOD = 2_000
CAT_GROOMING = 3_000

# ===================
# Константы Алисы
# ===================
ALICE_START_BALANCE = 100_000
ALICE_SALARY = 200_000
LOAN_AMOUNT = 10_000_000
LOAN_RATE = 0.12
LOAN_YEARS = 15
ALICE_FOOD = 4_000
ALICE_TRANSPORT = 1_500
DOG_PRIZE = 100_000
DOG_WIN_PROB = 0.25
DOG_FOOD = 2_000
DOG_GROOMING = 5_000


class Person:
    def __init__(self, name, balance, salary, expenses=None, incomes=None):
        self.name = name
        self.balance = balance
        self.salary = salary
        self.expenses = expenses if expenses else []
        self.incomes = incomes if incomes else []

    def monthly_update(self, month):
        # считаем расходы
        total_expenses = 0
        for expense in self.expenses:
            if callable(expense):
                monthly_expense = expense(month)
            else:
                monthly_expense = expense
            total_expenses += monthly_expense

        # считаем доходы
        extra_income = 0
        for income in self.incomes:
            if callable(income):
                monthly_income = income(month)
            else:
                monthly_income = income
            extra_income += monthly_income

        total_income = self.salary + extra_income

        # обновляем баланс
        self.balance += total_income - total_expenses

    def __str__(self):
        return f"{self.name} накопит: {self.balance:,.0f} руб."


def annuity_payment(loan_amount, loan_rate, loan_years):
    months = loan_years * 12
    monthly_rate = loan_rate / 12

    numerator = loan_amount * monthly_rate * (1 + monthly_rate) ** months
    denominator = (1 + monthly_rate) ** months - 1

    monthly_payment = numerator / denominator
    return monthly_payment


# --- Вспомогательные функции расходов ---
def rent_with_indexation(month):
    year = month // 12
    return BOB_RENT_START * (1 + BOB_RENT_INDEXATION) ** year


def cat_grooming(month):
    return CAT_GROOMING if month % 2 == 0 else 0


def dog_grooming(month):
    return DOG_GROOMING if month % 2 != 0 else 0


def mortgage(month):
    monthly_mortgage = annuity_payment(LOAN_AMOUNT, LOAN_RATE, LOAN_YEARS)
    return monthly_mortgage if month < LOAN_YEARS * 12 else 0


# --- Дополнительный доход ---
def dogshow(month):
    return DOG_PRIZE if random.random() < DOG_WIN_PROB else 0


# --- Основная функция симуляции ---
def simulate(years):
    months = math.floor(years * 12)

    # --- Bob ---
    bob = Person(
        name="Боб",
        balance=BOB_START_BALANCE,
        salary=BOB_SALARY,
        expenses=[
            rent_with_indexation,
            BOB_FOOD,
            BOB_TRANSPORT,
            CAT_FOOD,
            cat_grooming
        ]
    )

    # --- Alice ---
    alice = Person(
        name="Алиса",
        balance=ALICE_START_BALANCE,
        salary=ALICE_SALARY,
        expenses=[
            mortgage,
            ALICE_FOOD,
            ALICE_TRANSPORT,
            DOG_FOOD,
            dog_grooming
        ],
        incomes=[
            dogshow
        ]
    )

    # --- Симуляция ---
    for month in range(months):
        bob.monthly_update(month)
        alice.monthly_update(month)

        # Ежегодный отчёт
        if (month + 1) % 12 == 0:
            year = (month + 1) // 12
            print(f"Год {year}:")
            print(bob)
            print(alice)
            print("-")

    print(f"\nЧерез {years} лет:\n{bob}\n{alice}")

if __name__ == "__main__":
    years_to_simulate = float(input("Введите количество лет для симуляции: "))
    simulate(years_to_simulate)