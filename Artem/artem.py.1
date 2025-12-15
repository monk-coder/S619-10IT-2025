while True:
    try:
        years = int(input("количество лет: "))
        if 1 <= years <= 100:
            break
        else:
            print("Ошибка. Количество лет от 1 до 100")
    except ValueError:
        print("Ошибка. Напишите только число")

while True: 
    try:
        nomer_mes = int(input("месяц: "))
        if 0 <= nomer_mes <= 12:
            break
        else:
            print("Ошибка. Введите номер месяца от 1 до 12")
    except ValueError:
        print("Ошибка. Напишите только число")

class Person:
    def __init__(self, name, salary, rent=0, food=0, loan=0, transport=0, balance=0):
        self.name = name
        self.salary = salary
        self.rent = rent
        self.food = food
        self.transport = transport
        self.loan = round((loan * 0.12) / 12, 2) if loan > 0 else 0
        self.balance = balance

    def calculate_monthly_income(self):
        # доход за 1 месяц:
        expenses = self.rent + self.food + self.transport + self.loan
        return self.salary - expenses

    def get_total_income(self, months):
        # общий доход
        return self.calculate_monthly_income() * months

    def update_balance(self, months):
        balances = []
        current_balance = self.balance
        monthly_net = self.calculate_monthly_income()
        for _ in range(months):
            current_balance += monthly_net
            balances.append(current_balance)
        return balances

loan_value = 100000
bob = Person(
    name='Bob',
    salary=80000,
    rent=30000,
    food=4000,
    transport=1500,
    balance=200000
)
alice = Person(
    name='Alice',
    salary=200000,
    loan=loan_value,
    food=4000,
    transport=1500,
    balance=100000
)


months_total = years * 12 + nomer_mes #количество месяцев


bob_balances = bob.update_balance(months_total)
alice_balances = alice.update_balance(months_total)

print("Bob")
print(f"Ежемесячный чистый доход: {bob.calculate_monthly_income():} рублей")
print(f"Общий чистый доход за {months_total} месяцев: {bob.get_total_income(months_total):} рублей")
print()
print("Alice")
print(f"Ежемесячный чистый доход: {alice.calculate_monthly_income():} рублей")
print(f"Общий чистый доход за {months_total} месяцев: {alice.get_total_income(months_total):} рублей")
print()

for g in range(len(bob_balances)):
    month_num = g + 1
    print(f"{month_num} месяц:")
    print(f"- Баланс Боба: {bob_balances[g]:} рублей")
    print(f"- Баланс Алисы: {alice_balances[g]:} рублей")
