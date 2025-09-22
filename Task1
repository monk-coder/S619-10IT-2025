# Базовый класс для всех персонажей  
class Person:
    def __init__(self, name, initial_capital, salary, food, transport):
        self.name = name          # Имя персонажа  
        self.capital = initial_capital  # Начальный капитал  
        self.salary = salary      # Зарплата в месяц  
        self.food = food          # Расходы на еду в месяц  
        self.transport = transport  # Расходы на транспорт в месяц

    # Расчет общего дохода за указанное количество лет  
    def calculate_income(self, years):
        return self.capital + (self.salary * 12 * years)

# Класс для Боба (наследуется от Person)
class Bob(Person):
    def __init__(self):
        # Вызов конструктора родительского класса с параметрами Боба  
        super().__init__("Боб", 100000, 80000, 4000, 1500)
        self.cat_food = 2000     # Расходы на еду кота в месяц  
        self.cat_care = 1500     # Расходы на уход за котом в месяц

    # Расчет расходов Боба  
    def calculate_expenses(self, years):
        apartment = 30000 * (1.05 ** years)  # Аренда с учетом роста цен  
        total_apartment = apartment * 12 * years  
        other = (self.food + self.transport + self.cat_food + self.cat_care) * 12 * years  
        return total_apartment + other

# Класс для Алисы (наследуется от Person)
class Alice(Person):
    def __init__(self):
        # Вызов конструктора родительского класса с параметрами Алисы  
        super().__init__("Алиса", 100000, 200000, 4000, 1500)
        self.mortgage = 100000     # Ежемесячный платеж по ипотеке (1% от 10 млн)

    # Расчет расходов Алисы  
    def calculate_expenses(self, years):
        if years <= 30:
            return (self.mortgage + self.food + self.transport) * 12 * years  
        else:
            # После 30 лет ипотека уже выплачена  
            return (self.mortgage * 12 * 30) + (self.food + self.transport) * 12 * years

# Основной код программы  
years = float(input("Введите количество лет для расчета: "))

# Создаем персонажей  
bob = Bob()
alice = Alice()

# Выводим результаты  
print(f"\nЧерез {years} лет:")
print(f"{bob.name}: {bob.calculate_income(years) - bob.calculate_expenses(years):,.2f} руб.")
print(f"{alice.name}: {alice.calculate_income(years) - alice.calculate_expenses(years):,.2f} руб.")
