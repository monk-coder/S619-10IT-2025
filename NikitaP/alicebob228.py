import numpy as np

# ===================== ИСХОДНЫЕ ДАННЫЕ =====================
# Боб
bob_start_capital = 100000
bob_salary = 80000
bob_rent = 30000
bob_food = 4000
bob_transport = 1500
bob_cat_food = 2000
bob_cat_grooming = 3000  # раз в 2 месяца

# Алиса
alice_start_capital = 100000
alice_salary = 200000
alice_apartment_price = 10000000
alice_food = 4000
alice_transport = 1500

# Новая собака Алисы
alice_dog_initial_age = 10  # лет
alice_dog_food = 10000
alice_dog_care = 5000
alice_has_dog = True

# Ипотечные параметры Алисы
down_payment_percent = 0.15  # 15% первоначальный взнос
mortgage_rate = 0.12  # 12% годовых
mortgage_years = 20  # срок ипотеки

# Другие параметры
months_in_year = 12
bob_other_expenses = 10000
alice_other_expenses = 130000

# ===================== ФУНКЦИИ ДЛЯ РАСЧЕТОВ =====================
def calculate_mortgage_payment(apartment_price, down_payment_percent, annual_rate, years):
    """
    Расчет аннуитетного платежа по ипотеке
    Формула: P = S * (i * (1 + i)^n) / ((1 + i)^n - 1)
    где P - платеж, S - сумма кредита, i - месячная ставка, n - количество месяцев
    """
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
    """
    Обновление статуса собаки
    Собака умирает, когда достигает определенного возраста (например, 15 лет)
    или с вероятностью, которая увеличивается с возрастом
    """
    if not has_dog:
        return current_age, False, has_dog
    
    # Собака стареет на 1/12 года каждый месяц
    new_age = current_age + (1 / 12)
    
    # Вероятность смерти увеличивается после 10 лет
    death_probability = 0
    if new_age >= 15:
        death_probability = 1.0  # гарантированная смерть к 15 годам
    elif new_age > 10:
        death_probability = 0.01 + (new_age - 10) * 0.02  # увеличивается с возрастом
    
    # Проверяем, умерла ли собака в этом месяце
    if np.random.random() < death_probability:
        print(f"  Месяц {month_counter}: У Алисы умерла собака в возрасте {new_age:.1f} лет")
        has_dog = False
        return new_age, False, has_dog
    
    return new_age, True, has_dog

def calculate_monthly_expenses_alice(month, dog_age, dog_alive, food_cost, dog_food_cost):
    """
    Расчет месячных расходов Алисы
    """
    # Базовые расходы
    expenses = food_cost + alice_transport + alice_other_expenses
    
    # Расходы на собаку, если она жива
    if dog_alive:
        expenses += dog_food_cost + alice_dog_care
    
    return expenses, food_cost, dog_food_cost

def calculate_monthly_expenses_bob(month, rent, food_cost, cat_food_cost, salary):
    """
    Расчет месячных расходов Боба
    """
    # Базовая аренда
    current_rent = rent
    
    # Индексация аренды раз в год на 5%
    if month % 12 == 0 and month > 0:
        current_rent *= 1.05
    
    # Расходы на кота (стрижка раз в 2 месяца)
    cat_grooming = bob_cat_grooming if month % 2 == 0 else 0
    cat_expenses = cat_food_cost + cat_grooming
    
    # Инфляция на продукты и корм для кота
    current_food = food_cost
    current_cat_food = cat_food_cost
    if month % 12 == 0 and month > 0:
        current_food *= 1.07
        current_cat_food *= 1.07
    
    # Общие расходы
    expenses = current_rent + current_food + bob_transport + cat_expenses + bob_other_expenses
    
    return expenses, current_rent, current_food, current_cat_food

def calculate_income_bob(month, salary):
    """
    Расчет дохода Боба с учетом чаевых и индексации зарплаты
    """
    current_salary = salary
    
    # Чаевые (в среднем 10,000 руб/мес, но с сезонностью)
    tips_base = 10000
    if month % 12 in [5, 6, 7]:  # лето
        tips = tips_base * 1.3
    elif month % 12 == 11:  # декабрь
        tips = tips_base * 1.3
    elif month % 12 in [0, 1]:  # январь-февраль
        tips = tips_base * 0.8
    else:
        tips = tips_base
    
    # Индексация зарплаты раз в год (70% вероятность)
    if month % 12 == 0 and month > 0:
        if np.random.random() < 0.7:
            current_salary *= 1.05
    
    return current_salary + tips, current_salary

def calculate_income_alice(month, salary):
    """
    Расчет дохода Алисы с учетом бонусов и индексации
    """
    current_salary = salary
    
    # Годовой бонус в декабре (50% от оклада с 90% вероятностью)
    bonus = 0
    if month % 12 == 11:  # декабрь
        if np.random.random() < 0.9:
            bonus = current_salary * 0.5
    
    # Индексация зарплаты раз в год на 7%
    if month % 12 == 0 and month > 0:
        current_salary *= 1.07
    
    return current_salary + bonus, current_salary

# ===================== ОСНОВНАЯ ФУНКЦИЯ РАСЧЕТА =====================
def calculate_finances(bob_start, alice_start, years, detailed_output=False):
    bob_capital = bob_start
    alice_capital = alice_start
    
    # Локальные копии переменных
    bob_current_rent = bob_rent
    bob_current_food = bob_food
    bob_current_cat_food = bob_cat_food
    bob_current_salary = bob_salary
    
    alice_current_food = alice_food
    alice_current_dog_food = alice_dog_food
    alice_current_salary = alice_salary
    has_dog = alice_has_dog
    
    # Расчет ипотечного платежа Алисы
    alice_monthly_mortgage, alice_loan_amount = calculate_mortgage_payment(
        alice_apartment_price, down_payment_percent, mortgage_rate, mortgage_years
    )
    
    # Начальные значения
    dog_age = alice_dog_initial_age
    alice_mortgage_remaining = alice_loan_amount
    total_months = years * months_in_year
    
    if detailed_output:
        print(f"\nНачальные условия для {years} лет:")
        print(f"  Ипотека Алисы: платеж {alice_monthly_mortgage:,.2f} руб/мес")
        print(f"  Остаток кредита: {alice_mortgage_remaining:,.2f} руб")
        print(f"  Собака Алисы: {dog_age} лет")
    
    for month in range(total_months):
        # ===== БОБ =====
        bob_income, bob_current_salary = calculate_income_bob(month, bob_current_salary)
        bob_expenses, bob_current_rent, bob_current_food, bob_current_cat_food = calculate_monthly_expenses_bob(
            month, bob_current_rent, bob_current_food, bob_current_cat_food, bob_current_salary
        )
        bob_capital += bob_income - bob_expenses
        
        # ===== АЛИСА =====
        alice_income, alice_current_salary = calculate_income_alice(month, alice_current_salary)
        
        # Обновляем статус собаки и возраст
        dog_age, dog_alive, has_dog = update_dog_status(dog_age, month + 1, has_dog)
        
        # Расходы Алисы
        alice_expenses, alice_current_food, alice_current_dog_food = calculate_monthly_expenses_alice(
            month, dog_age, dog_alive, alice_current_food, alice_current_dog_food
        )
        
        # Ипотечный платеж
        if alice_mortgage_remaining > 0:
            # Проценты за месяц
            monthly_interest = alice_mortgage_remaining * mortgage_rate / 12
            # Основной долг
            principal = alice_monthly_mortgage - monthly_interest
            alice_mortgage_remaining -= principal
            alice_expenses += alice_monthly_mortgage
            
            # Досрочное погашение из годового бонуса (если есть)
            if month % 12 == 11 and alice_income > alice_current_salary * 1.4:  # декабрь с бонусом
                extra_payment = (alice_income - alice_current_salary) * 0.5  # 50% бонуса на досрочку
                alice_mortgage_remaining = max(0, alice_mortgage_remaining - extra_payment)
                if extra_payment > 0:
                    print(f"  Месяц {month+1}: Алиса внесла досрочное погашение {extra_payment:,.0f} руб")
        
        alice_capital += alice_income - alice_expenses
        
        # Инфляция для Алисы (ежегодно)
        if month % 12 == 0 and month > 0:
            alice_current_food *= 1.07
            if dog_alive:
                alice_current_dog_food *= 1.07
        
        # Вывод детальной информации (только для коротких периодов)
        if detailed_output and years <= 5 and month < 24:
            if month % 6 == 0 or (not dog_alive and has_dog):
                print(f"  Месяц {month + 1}: "
                      f"Боб: +{bob_income:,.0f} -{bob_expenses:,.0f} = {bob_capital:,.0f} | "
                      f"Алиса: +{alice_income:,.0f} -{alice_expenses:,.0f} = {alice_capital:,.0f}")
    
    # Чистая стоимость Алисы (с учетом квартиры и остатка ипотеки)
    alice_net_worth = alice_capital + alice_apartment_price - max(0, alice_mortgage_remaining)
    
    return bob_capital, alice_capital, alice_net_worth, alice_mortgage_remaining, has_dog, bob_current_rent, bob_current_salary, alice_current_salary

# ===================== ВЫПОЛНЕНИЕ ПРОГРАММЫ =====================
def main():
    print("=" * 60)
    print("ФИНАНСОВАЯ СИМУЛЯЦИЯ: БОБ И АЛИСА")
    print("=" * 60)
    
    # Стандартные периоды
    periods = [1, 5, 10, 20]
    
    print("\nСтандартные периоды:")
    for years in periods:
        bob_final, alice_final, alice_net_worth, alice_mortgage, dog_alive, bob_rent_final, bob_salary_final, alice_salary_final = calculate_finances(
            bob_start_capital, alice_start_capital, years, detailed_output=(years <= 5)
        )
        
        print(f"\nЧерез {years} год(а/лет):")
        print(f"  Боб: {bob_final:,.2f} руб.")
        print(f"  Алиса (на счету): {alice_final:,.2f} руб.")
        print(f"  Алиса (чистая стоимость): {alice_net_worth:,.2f} руб.")
        if alice_mortgage > 0:
            print(f"  Остаток ипотеки: {alice_mortgage:,.2f} руб.")
        else:
            print(f"  Ипотека: полностью погашена!")
        print(f"  Собака: {'жива' if dog_alive else 'умерла'}")
    
    # Запрос пользовательского ввода
    print("\n" + "=" * 60)
    try:
        user_years = int(input("Введите количество лет для симуляции (1-30): "))
        if 1 <= user_years <= 30:
            bob_bal, alice_bal, alice_net, alice_mort, dog_alive, bob_rent_final, bob_salary_final, alice_salary_final = calculate_finances(
                bob_start_capital, alice_start_capital, user_years, detailed_output=True
            )
            
            print(f"\n" + "=" * 60)
            print(f"ИТОГИ ЧЕРЕЗ {user_years} ЛЕТ:")
            print("=" * 60)
            print(f"\nБОБ:")
            print(f"  Накопления: {bob_bal:,.2f} рублей")
            print(f"  Аренда: {bob_rent_final:,.2f} руб/мес")
            print(f"  Зарплата: {bob_salary_final:,.2f} руб/мес")
            
            print(f"\nАЛИСА:")
            print(f"  Накопления: {alice_bal:,.2f} рублей")
            print(f"  Чистая стоимость: {alice_net:,.2f} рублей")
            print(f"  Зарплата: {alice_salary_final:,.2f} руб/мес")
            
            if alice_mort > 0:
                print(f"  Остаток ипотеки: {alice_mort:,.2f} рублей")
            else:
                print(f"  Ипотека: полностью погашена!")
            
            print(f"  Собака: {'жива' if dog_alive else 'умерла'}")
            
            # Сравнение
            print(f"\nСРАВНЕНИЕ:")
            print(f"  Разница в накоплениях: {alice_bal - bob_bal:,.2f} рублей")
            print(f"  Алиса богаче Боба на: {alice_net - bob_bal:,.2f} рублей")
        else:
            print("Пожалуйста, введите число от 1 до 30.")
    except ValueError:
        print("Ошибка: введите целое число.")

# Запуск программы
if __name__ == "__main__":
    # Установка seed для воспроизводимости результатов
    np.random.seed(42)
    main()
