#include <iostream>
#include <iomanip>
#include <cmath> // Для pow

// Общий класс для расходов и доходов
class PersonExpenses {
protected:
    double salary;
    double food_expenses;
    double transport_expenses;
    double savings;
    int months;                 // Прошедшие месяцы

public:
    PersonExpenses(double sal, double food, double transport)
        : salary(sal), food_expenses(food), transport_expenses(transport),
        savings(0), months(0) {}

    virtual ~PersonExpenses() = default;

    virtual void simulateMonth() = 0; // Чисто виртуальный метод для переработки в наследниках

    void addIncome(double amount) {
        savings += amount;
    }

    virtual void printStatus() const = 0;
};

// Класс для Боба
class Bob : public PersonExpenses {
private:
    double rent;                // руб/мес
    double cat_food;            // руб/мес
    double cat_grooming;        // руб раз в 2 месяца
    int months_since_rent_increase;

public:
    Bob()
        : PersonExpenses(80000, 4000, 1500),
        rent(30000),
        cat_food(2000),
        cat_grooming(3000),
        months_since_rent_increase(0) {}

    void simulateMonth() override {
        months++;
        months_since_rent_increase++;

        // Индексация аренды раз в 12 месяцев на 5%
        if (months % 12 == 1 && months != 1) {
            rent *= 1.05;
        }

        // Расходы на кота: еда каждый месяц, стрижка и мойка раз в 2 месяца
        double cat_grooming_this_month = (months % 2 == 0) ? cat_grooming : 0;

        double total_expenses = rent + food_expenses + transport_expenses + cat_food + cat_grooming_this_month;

        addIncome(salary - total_expenses);
    }

    void printStatus() const override {
        std::cout << "Bob's status after " << months << " months:\n";
        std::cout << "  Savings: " << std::fixed << std::setprecision(2) << savings << " rub\n";
        std::cout << "  Current rent: " << rent << " rub/month\n";
    }
};

// Класс для Алисы
class Alice : public PersonExpenses {
private:
    double apartment_cost;     // стоимость квартиры
    // Ипотека параметры
    double annual_interest_rate; // 12% годовых
    int loan_term_months;        // срок ипотеки в месяцах
    double monthly_payment;      // ежемесячный платёж по ипотеке
    double loan_balance;         // остаток долга

public:
    Alice()
        : PersonExpenses(200000, 4000, 1500),
        apartment_cost(10000000),
        annual_interest_rate(0.12),
        loan_term_months(240) // 20 лет
    {
        loan_balance = apartment_cost;
        monthly_payment = calculateMonthlyPayment(loan_balance, annual_interest_rate, loan_term_months);
    }

    double calculateMonthlyPayment(double principal, double annual_rate, int months) {
        double monthly_rate = annual_rate / 12.0;
        return principal * (monthly_rate * pow(1 + monthly_rate, months)) /
            (pow(1 + monthly_rate, months) - 1);
    }

    void simulateMonth() override {
        months++;

        // Платёж по ипотеке
        double monthly_rate = annual_interest_rate / 12.0;
        double interest = loan_balance * monthly_rate;
        double principal_payment = monthly_payment - interest;
        // Общая сумма ежемесячного платежа по ипотеке(monthly_payment);
        // Часть, которая идет на погашение основного долга(principal_payment); 
        // Оставшаяся часть — это проценты за этот месяц(interest).

        loan_balance -= principal_payment;
        if (loan_balance < 0) loan_balance = 0;

        double total_expenses = food_expenses + transport_expenses + monthly_payment;

        addIncome(salary - total_expenses);
    }

    void printStatus() const override {
        std::cout << "Alice's status after " << months << " months:\n";
        std::cout << "  Savings: " << std::fixed << std::setprecision(2) << savings << " rub\n";
        std::cout << "  Remaining loan balance: " << loan_balance << " rub\n";
        std::cout << "  Monthly mortgage payment: " << monthly_payment << " rub\n";
    }
};

int main() {
    Bob bob;
    Alice alice;

    int simulation_months = 60; // симуляция на 5 лет

    for (int i = 1; i <= simulation_months; ++i) {
        bob.simulateMonth();
        alice.simulateMonth();

        // Для примера выводим статус каждый год
        if (i % 12 == 0) {
            std::cout << "=== After " << i / 12 << " year(s) ===\n";
            bob.printStatus();
            alice.printStatus();
            std::cout << std::endl;
        }
    }

    return 0;
}
