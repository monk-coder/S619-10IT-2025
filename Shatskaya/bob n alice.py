class Human:
    def init(self, zp, name, rent, food, transport, cat_food, cat_care, rent_proc=0, rent_time=0, apartment_cost=0):
        self.zp = zp
        self.name = name
        self.rent = rent
        self.food = food
        self.transport = transport
        self.cat_food = cat_food
        self.cat_care = cat_care
        self.rent_proc = rent_proc
        self.rent_time = rent_time
        self.apartment_cost = apartment_cost

Bob = Human(
    name='Bob',
    zp=80000,
    rent=30000,
    food=4000,
    transport=1500,
    cat_food=2000,
    cat_care=1500,  #тк 3000 раз в два месяца
    rent_proc=0,
    rent_time=0
)

Alice = Human(
    name='Alice',
    zp=200000,
    rent=0,
    food=4000,
    transport=1500,
    cat_food=0,
    cat_care=0,
    rent_proc=0.12,
    rent_time=30,
    apartment_cost=10000000
)

def calculate_mortgage(apartment_cost, rent_proc, rent_time):
    """Расчет аннуитетного платежа по ипотеке"""
    if rent_proc == 0:
        return 0
    
    months = rent_time * 12
    monthly_rate = rent_proc / 12
    annuity_coef = (monthly_rate * (1 + monthly_rate)  months) / ((1 + monthly_rate)  months - 1)
    monthly_payment = apartment_cost * annuity_coef
    return monthly_payment

years_sim = int(input('Сколько прошло лет: '))

monthly_mortgage = calculate_mortgage(Alice.apartment_cost, Alice.rent_proc, Alice.rent_time)
yearly_mortgage = monthly_mortgage * 12

bob_monthly_expenses = Bob.food + Bob.transport + Bob.cat_food + Bob.cat_care
alice_monthly_expenses = Alice.food + Alice.transport

yearly_zp_bob = Bob.zp * 12
yearly_zp_alice = Alice.zp * 12
yearly_expenses_bob = bob_monthly_expenses * 12
yearly_expenses_alice = alice_monthly_expenses * 12

Bbalance = 0
Abalance = 0

current_rent = Bob.rent
for year in range(years_sim):
    yearly_rent_bob = current_rent * 12
    Bbalance += (yearly_zp_bob - yearly_rent_bob - yearly_expenses_bob)
    
    Abalance += (yearly_zp_alice - yearly_mortgage - yearly_expenses_alice)
    
    current_rent *= 1.05

print(f'Через {years_sim} лет:')

if Abalance > 0:
    print(f'Алиса накопит: {Abalance:.1f} руб.')
else:
    print(f'Алиса потратит: {Abalance:.1f} руб.')

if Bbalance > 0:
    print(f'Боб накопит: {Bbalance:.1f} руб.')
else:
    print(f'Боб потратит: {Bbalance:.1f} руб.')