import numpy as np

# ===================== ИСХОДНЫЕ ДАННЫЕ (КОНСТАНТЫ) =====================
# Боб
BOB_START_CAPITAL = 100_000
BOB_SALARY = 80_000
BOB_RENT = 30_000
BOB_FOOD = 4_000
BOB_TRANSPORT = 1_500
BOB_CAT_FOOD = 2_000
BOB_CAT_GROOMING = 3_000
BOB_OTHER_EXPENSES = 10_000

# Алиса
ALICE_START_CAPITAL = 100_000
ALICE_SALARY = 200_000
ALICE_APARTMENT_PRICE = 10_000_000
ALICE_FOOD = 4_000
ALICE_TRANSPORT = 1_500
ALICE_OTHER_EXPENSES = 130_000

# Новая собака Алисы
ALICE_DOG_INITIAL_AGE = 10
ALICE_DOG_FOOD = 10_000
ALICE_DOG_CARE = 5_000

# Ипотечные параметры Алисы
DOWN_PAYMENT_PERCENT = 0.15
MORTGAGE_RATE = 0.12
MORTGAGE_YEARS = 20

# Другие параметры
MONTHS_IN_YEAR = 12
INFLATION_RATE = 0.07
RENT_INCREASE_RATE = 0.05
SALARY_INCREASE_BOB_PROB = 0.7
SALARY_INCREASE_BOB_RATE = 0.05
SALARY_INCREASE_ALICE_RATE = 0.07
BONUS_PROBABILITY = 0.9
BONUS_PERCENT = 0.5

# Чаевые Боба
TIPS_BASE = 10_000
TIPS_SUMMER_MULTIPLIER = 1.3
TIPS_WINTER_MULTIPLIER = 0.8
TIPS_DECEMBER_MULTIPLIER = 1.3

# ===================== ФУНКЦИИ ДЛЯ РАСЧЕТОВ =====================
def calculate_mortgage_payment(apartment_price, down_payment_percent, annual_rate, years):
    down_payment = apartment_price * down_payment_percent
    loan_amount = apartment_price - down_payment
    monthly_rate = annual_rate / 12
    total_months = years * 12
    
    if monthly_rate == 0:
        monthly_payment = loan_amount / total_months
    else:
        monthly_payment = (loan_amount * monthly_rate * (1 + monthly_rate)**total_months) / \
                         ((1 + monthly_rate)**total_months - 1)
    
    return monthly_payment, loan_amount

def update_dog_status(current_age, month_counter, has_dog):
    if not has_dog:
        return current_age, False, has_dog
    
    new_age = current_age + (1 / 12)
    
    death_probability = 0
    if new_age >= 15:
        death_probability = 1.0
    elif new_age > 10:
        death_probability = 0.01 + (new_age - 10) * 0.02
    
    if np.random.random() < death_probability:
        print(f"  Месяц {month_counter}: У Алисы умерла собака в возрасте {new_age:.1f} лет")
        has_dog = False
        return new_age, False, has_dog
    
    return new_age, True, has_dog

def calculate_monthly_expenses_alice(month, dog_age, dog_alive, food_cost, dog_food_cost):
    expenses = food_cost + ALICE_TRANSPORT + ALICE_OTHER_EXPENSES
    
    if dog_alive:
        expenses += dog_food_cost + ALICE_DOG_CARE
    
    return expenses, food_cost, dog_food_cost

def calculate_monthly_expenses_bob(month, rent, food_cost, cat_food_cost, salary):
    current_rent = rent
    
    if month % MONTHS_IN_YEAR == 0 and month > 0:
        current_rent *= (1 + RENT_INCREASE_RATE)
    
    cat_grooming = BOB_CAT_GROOMING if month % 2 == 0 else 0
    cat_expenses = cat_food_cost + cat_grooming
    
    current_food = food_cost
    current_cat_food = cat_food_cost
    if month % MONTHS_IN_YEAR == 0 and month > 0:
        current_food *= (1 + INFLATION_RATE)
        current_cat_food *= (1 + INFLATION_RATE)
    
    expenses = current_rent + current_food + BOB_TRANSPORT + cat_expenses + BOB_OTHER_EXPENSES
    
    return expenses, current_rent, current_food, current_cat_food

def calculate_income_bob(month, salary):
    current_salary = salary
    
    if month % MONTHS_IN_YEAR in [5, 6, 7]:
        tips = TIPS_BASE * TIPS_SUMMER_MULTIPLIER
    elif month % MONTHS_IN_YEAR == 11:
        tips = TIPS_BASE * TIPS_DECEMBER_MULTIPLIER
    elif month % MONTHS_IN_YEAR in [0, 1]:
        tips = TIPS_BASE * TIPS_WINTER_MULTIPLIER
    else:
        tips = TIPS_BASE
    
    if month % MONTHS_IN_YEAR == 0 and month > 0:
        if np.random.random() < SALARY_INCREASE_BOB_PROB:
            current_salary *= (1 + SALARY_INCREASE_BOB_RATE)
    
    return current_salary + tips, current_salary

def calculate_income_alice(month, salary):
    current_salary = salary
    
    bonus = 0
    if month % MONTHS_IN_YEAR == 11:
        if np.random.random() < BONUS_PROBABILITY:
            bonus = current_salary * BONUS_PERCENT
    
    if month % MONTHS_IN_YEAR == 0 and month > 0:
        current_salary *= (1 + SALARY_INCREASE_ALICE_RATE)
    
    return current_salary + bonus, current_salary

# ===================== ОСНОВНАЯ ФУНКЦИЯ РАСЧЕТА =====================
def calculate_finances(bob_start, alice_start, years, detailed_output=False):
    bob_capital = bob_start
    alice_capital = alice_start
    
    bob_current_rent = BOB_RENT
    bob_current_food = BOB_FOOD
    bob_current_cat_food = BOB_CAT_FOOD
    bob_current_salary = BOB_SALARY
    
    alice_current_food = ALICE_FOOD
    alice_current_dog_food = ALICE_DOG_FOOD
    alice_current_salary = ALICE_SALARY
    has_dog = True
    
    alice_monthly_mortgage, alice_loan_amount = calculate_mortgage_payment(
        ALICE_APARTMENT_PRICE, DOWN_PAYMENT_PERCENT, MORTGAGE_RATE, MORTGAGE_YEARS
    )
    
    dog_age = ALICE_DOG_INITIAL_AGE
    alice_mortgage_remaining = alice_loan_amount
    total_months = years * MONTHS_IN_YEAR
    
    if detailed_output:
        print(f"\nНачальные условия для {years} лет:")
        print(f"  Ипотека Алисы: платеж {alice_monthly_mortgage:,.2f} руб/мес")
        print(f"  Остаток кредита: {alice_mortgage_remaining:,.2f} руб")
        print(f"  Собака Алисы: {dog_age} лет")
    
    for month in range(total_months):
        bob_income, bob_current_salary = calculate_income_bob(month, bob_current_salary)
        bob_expenses, bob_current_rent, bob_current_food, bob_current_cat_food = calculate_monthly_expenses_bob(
            month, bob_current_rent, bob_current_food, bob_current_cat_food, bob_current_salary
        )
        bob_capital += bob_income - bob_expenses
        
        alice_income, alice_current_salary = calculate_income_alice(month, alice_current_salary)
        
        dog_age, dog_alive, has_dog = update_dog_status(dog_age, month + 1, has_dog)
        
        alice_expenses, alice_current_food, alice_current_dog_food = calculate_monthly_expenses_alice(
            month, dog_age, dog_alive, alice_current_food, alice_current_dog_food
        )
        
        if alice_mortgage_remaining > 0:
            monthly_interest = alice_mortgage_remaining * MORTGAGE_RATE / 12
            principal = alice_monthly_mortgage - monthly_interest
            alice_mortgage_remaining -= principal
            alice_expenses += alice_monthly_mortgage
            
            if month % MONTHS_IN_YEAR == 11 and alice_income > alice_current_salary * 1.4:
                extra_payment = (alice_income - alice_current_salary) * 0.5
                alice_mortgage_remaining = max(0, alice_mortgage_remaining - extra_payment)
                if extra_payment > 0 and detailed_output:
                    print(f"  Месяц {month+1}: Алиса внесла досрочное погашение {extra_payment:,.0f} руб")
        
        alice_capital += alice_income - alice_expenses
        
        if month % MONTHS_IN_YEAR == 0 and month > 0:
            alice_current_food *= (1 + INFLATION_RATE)
            if dog_alive:
                alice_current_dog_food *= (1 + INFLATION_RATE)
        
        if detailed_output and years <= 5 and month < 24:
            if month % 6 == 0 or (not dog_alive and has_dog):
                print(f"  Месяц {month + 1}: "
                      f"Боб: +{bob_income:,.0f} -{bob_expenses:,.0f} = {bob_capital:,.0f} | "
                      f"Алиса: +{alice_income:,.0f} -{alice_expenses:,.0f} = {alice_capital:,.0f}")
    
    alice_net_worth = alice_capital + ALICE_APARTMENT_PRICE - max(0, alice_mortgage_remaining)
    
    return bob_capital, alice_capital, alice_net_worth, alice_mortgage_remaining, has_dog, bob_current_rent, bob_current_salary, alice_current_salary, alice_loan_amount

# ===================== ВЫПОЛНЕНИЕ ПРОГРАММЫ =====================
def main():
    print("=" * 60)
    print("ФИНАНСОВАЯ СИМУЛЯЦИЯ: БОБ И АЛИСА")
    print("=" * 60)
    
    periods = [1, 5, 10, 20]
    
    print("\nРЕЗУЛЬТАТЫ ДЛЯ СТАНДАРТНЫХ ПЕРИОДОВ:")
    for years in periods:
        bob_final, alice_final, alice_net_worth, alice_mortgage, dog_alive, bob_rent_final, bob_salary_final, alice_salary_final, alice_loan_amount = calculate_finances(
            BOB_START_CAPITAL, ALICE_START_CAPITAL, years, detailed_output=(years <= 5)
        )
        
        print(f"\nЧерез {years} год(а/лет):")
        print(f"  БОБ:")
        print(f"    Накопления: {bob_final:,.2f} руб.")
        print(f"    Зарплата: {bob_salary_final:,.2f} руб/мес")
        
        print(f"  АЛИСА:")
        print(f"    Накопления на счету: {alice_final:,.2f} руб.")
        print(f"    Чистая стоимость: {alice_net_worth:,.2f} руб.")
        if alice_mortgage > 0:
            print(f"    Остаток ипотеки: {alice_mortgage:,.2f} руб.")
        else:
            print(f"    Ипотека: полностью погашена!")
        print(f"    Собака: {'жива' if dog_alive else 'умерла'}")
    
    print("\n" + "=" * 60)
    try:
        user_years = int(input("Введите количество лет для симуляции (1-30): "))
        if 1 <= user_years <= 30:
            bob_bal, alice_bal, alice_net, alice_mort, dog_alive, bob_rent_final, bob_salary_final, alice_salary_final, alice_loan_amount = calculate_finances(
                BOB_START_CAPITAL, ALICE_START_CAPITAL, user_years, detailed_output=True
            )
            
            print(f"\n" + "=" * 60)
            print(f"ПОДРОБНЫЕ ИТОГИ ЧЕРЕЗ {user_years} ЛЕТ:")
            print("=" * 60)
            print(f"\nБОБ:")
            print(f"  Итоговые накопления: {bob_bal:,.2f} рублей")
            print(f"  Финальная зарплата: {bob_salary_final:,.2f} руб/мес")
            
            print(f"\nАЛИСА:")
            print(f"  Накопления на счетах: {alice_bal:,.2f} рублей")
            print(f"  Чистая стоимость: {alice_net:,.2f} рублей")
            print(f"  Финальная зарплата: {alice_salary_final:,.2f} руб/мес")
            
            if alice_mort > 0:
                print(f"  Остаток ипотеки: {alice_mort:,.2f} рублей")
                print(f"  Процент погашения ипотеки: {(1 - alice_mort/alice_loan_amount)*100:.1f}%")
            else:
                print(f"  Ипотека: полностью погашена!")
            
            print(f"  Собака: {'жива' if dog_alive else 'умерла'}")
            
            print(f"\nСРАВНЕНИЕ:")
            print(f"  Разница в накоплениях: {alice_bal - bob_bal:,.2f} рублей")
            print(f"  Алиса богаче Боба на: {alice_net - bob_bal:,.2f} рублей")
            
            print(f"\nАНАЛИЗ:")
            if alice_net > bob_bal * 2:
                print("  Вывод: Алиса значительно богаче Боба благодаря недвижимости")
            elif alice_net > bob_bal:
                print("  Вывод: Алиса богаче Боба, но разница не огромная")
            else:
                print("  Вывод: Боб сберег больше денег, но у Алисы есть недвижимость")
                
        else:
            print("Пожалуйста, введите число от 1 до 30.")
    except ValueError:
        print("Ошибка: введите целое число.")

# Запуск программы
if __name__ == "__main__":
    np.random.seed(42)
    main()
