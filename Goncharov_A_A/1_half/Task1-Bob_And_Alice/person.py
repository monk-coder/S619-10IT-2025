# person.py
class Person:
    def __init__(self, name, salary, expenses):
        self.name = name
        self.salary = salary
        self.expenses = expenses
        self.savings = 0
        
    def calculate_monthly_balance(self):
        total_expenses = sum(self.expenses.values())
        return self.salary - total_expenses
    
    def update_savings(self):
        monthly_balance = self.calculate_monthly_balance()
        self.savings += monthly_balance
        
    def __str__(self):
        return f"{self.name}: salary {self.salary} RUB, savings {self.savings} RUB"
