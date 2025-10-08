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

        self.mortgage_payment = (self.apartment_price * monthly_rate * 
                               (1 + monthly_rate) ** total_months) / ((1 + monthly_rate) ** total_months - 1)
        
        self.mortgage_balance = self.apartment_price
    
    def calculate_monthly_expenses(self):
        expenses = super().calculate_monthly_expenses()
        expenses += self.mortgage_payment
        
        interest = self.mortgage_balance * (self.mortgage_rate / 12)
        principal = self.mortgage_payment - interest
        self.mortgage_balance -= principal
        
        return expenses
    
    def get_apartment_equity(self):
        return max(0.0, self.apartment_price - self.mortgage_balance)


def get_simulation_period():
    while True:
        try:
            years = int(input("Введите количество лет для симуляции: "))
            if years < 0:
                print("Количество лет не может быть отрицательным. Попробуйте снова.")
                continue
            break
        except ValueError:
            print("Пожалуйста, введите целое число для количества лет.")
    
    while True:
        try:
            months = int(input("Введите количество месяцев для симуляции (1-12): "))
            if months < 1 or months > 12:
                print("Количество месяцев должно быть от 1 до 12. Попробуйте снова.")
                continue
            break
        except ValueError:
            print("Пожалуйста, введите целое число от 1 до 12 для количества месяцев.")
    
    return years, months


def run_simulation():
    years, months = get_simulation_period()
    total_months = years * 12 + months
    
    bob = Bob()
    alice = Alice()
    
    print(f"Симуляция жизни Bob и Alice на {years} лет и {months} месяцев")
    print(f"Bob: зарплата {bob.salary:,.2f} руб/мес, аренда {bob.rent:,.2f} руб/мес")
    print(f"Alice: зарплата {alice.salary:,.2f} руб/мес, ипотека {alice.mortgage_payment:,.2f} руб/мес")
    
    for month in range(1, total_months + 1):
        bob.live_month()
        alice.live_month()
        
        if month % 12 == 0:
            year = month // 12
            bob_total = bob.savings
            alice_total = alice.savings + alice.get_apartment_equity()
            difference = alice_total - bob_total

            print(f"Год {year}: Bob {bob.savings:,.2f} руб | Alice {alice_total:,.2f} руб | Разница: {difference:,.2f} руб")
    
    bob_total_wealth = bob.savings
    alice_total_wealth = alice.savings + alice.get_apartment_equity()
    wealth_difference = alice_total_wealth - bob_total_wealth

    print(f"ФИНАЛ: Bob (сбережения: {bob.savings:,.2f} руб, аренда: {bob.rent:,.2f} руб/мес) | Alice (сбережения: {alice.savings:,.2f} руб, доля в квартире: {alice.get_apartment_equity():,.2f} руб) | Общие активы: Bob {bob_total_wealth:,.2f} руб, Alice {alice_total_wealth:,.2f} руб | Разница: {wealth_difference:,.2f} руб в пользу {'Alice' if wealth_difference > 0 else 'Bob'}")


if __name__ == "__main__":
    run_simulation()