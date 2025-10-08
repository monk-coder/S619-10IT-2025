#include <iostream>
#include <iomanip>

class Bob {
private:
    double salary;          // руб/мес
    double rent;            // руб/мес
    double food_expenses;   // руб/мес
    double transport_expenses; // руб/мес
    double cat_food;        // руб/мес
    double cat_grooming;    // руб раз в 2 месяца
    double savings;         // накопления
    int months;             // прошедшие месяцы

public:
    Bob()
        : salary(80000), rent(30000), food_expenses(4000), transport_expenses(1500),
        cat_food(2000), cat_grooming(3000), savings(0), months(0) {}

    void simulateMonth() {
        months++;

        // Индексация аренды раз в 12 месяцев на 5%
        if (months % 12 == 1 && months != 1) {
            rent *= 1.05;
        }

        // Расходы на кота: еда каждый месяц, стрижка и мойка раз в 2 месяца
        double cat_grooming_this_month = (months % 2 == 0) ? cat_grooming : 0;

        double total_expenses = rent + food_expenses + transport_expenses + cat_food + cat_grooming_this_month;

        savings += salary - total_expenses;
    }

    void printStatus() const {
        std::cout << "Bob's status after " << months << " months:\n";
        std::cout << "  Savings: " << std::fixed << std::setprecision(2) << savings << " rub\n";
        std::cout << "  Current rent: " << rent << " rub/month\n";
    }
};

class Alice {
private:
    double salary;          // руб/мес
    double apartment_cost;  // стоимость квартиры
    double food_expenses;   // руб/мес
    double transport_expenses; // руб/мес
    double savings;         // накопления
    int months;             // прошедшие месяцы

    // Ипотека параметры
    double annual_interest_rate; // 12% годовых
    int loan_term_months;        // срок ипотеки в месяцах
    double monthly_payment;      // ежемесячный платёж по ипотеке
    double loan_balance;         // остаток долга

    // Рассчитаем ежемесячный платёж по ипотеке (аннуитет)
    double calculateMonthlyPayment(double principal, double annual_rate, int months) {
        double monthly_rate = annual_rate / 12.0;
        return principal * (monthly_rate * pow(1 + monthly_rate, months)) / (pow(1 + monthly_rate, months) - 1);
    }

public:
    Alice()
        : salary(200000), apartment_cost(10000000), food_expenses(4000), transport_expenses(1500),
        savings(0), months(0), annual_interest_rate(0.12), loan_term_months(240) // 20 лет
    {
        loan_balance = apartment_cost;
        monthly_payment = calculateMonthlyPayment(loan_balance, annual_interest_rate, loan_term_months);
    }

    void simulateMonth() {
        months++;

        // Платёж по ипотеке
        // Рассчитаем проценты за месяц и уменьшение основного долга
        double monthly_rate = annual_interest_rate / 12.0;
        double interest = loan_balance * monthly_rate;
        double principal_payment = monthly_payment - interest;
        loan_balance -= principal_payment;
        if (loan_balance < 0) loan_balance = 0;

        double total_expenses = food_expenses + transport_expenses + monthly_payment;

        savings += salary - total_expenses;
    }

    void printStatus() const {
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
