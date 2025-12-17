> piterskiy666:
# Исходные данные
bob_start_capital = 100000
alice_start_capital = 100000
bob_salary = 80000
alice_salary = 200000

# Расходы
bob_rent = 30000
alice_mortgage = (10000000 * 0.12) / 12  # ≈ 100,000 руб/мес
bob_pet_cost = 5000
bob_other_expenses = 10000
alice_other_expenses = 130000

months_in_year = 12
periods = [1, 5, 10, 100]

def calculate_finances(bob_start, alice_start, years):
    bob_capital = bob_start
    alice_capital = alice_start

    for month in range(years * months_in_year):
        # Боб
        bob_capital += bob_salary
        bob_capital -= (bob_rent + bob_pet_cost + bob_other_expenses)

        # Алиса
        alice_capital += alice_salary
        alice_capital -= (alice_mortgage + alice_other_expenses)

    return bob_capital, alice_capital

# Расчёт и вывод для стандартных периодов
print("Стандартные периоды:")
for years in periods:
    bob_final, alice_final = calculate_finances(bob_start_capital, alice_start_capital, years)
    print(f"Через {years} год(а/лет): Боб - {bob_final:,.2f} руб., Алиса - {alice_final:,.2f} руб.")

# Запрос пользовательского ввода
try:
    user_years = int(input("\nВведите количество лет (1–100): "))
    if 1 <= user_years <= 100:
        bob_bal, alice_bal = calculate_finances(bob_start_capital, alice_start_capital, user_years)
        print(f"\nЧерез {user_years} года(лет):")
        print(f"У Боба будет: {bob_bal:,.2f} рублей")
        print(f"У Алисы будет: {alice_bal:,.2f} рублей")
