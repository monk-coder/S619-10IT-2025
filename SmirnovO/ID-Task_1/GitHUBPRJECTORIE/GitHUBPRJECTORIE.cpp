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







import logging
import sqlite3
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import asyncio
from threading import Thread

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Конфигурация
TOKEN = "YOUR_BOT_TOKEN"
DATABASE_URL = "clicker_game.db"

app = Flask(__name__)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            chat_id INTEGER,
            score INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 100,
            max_energy INTEGER DEFAULT 100,
            last_energy_update INTEGER,
            level INTEGER DEFAULT 1,
            total_clicks INTEGER DEFAULT 0,
            double_click INTEGER DEFAULT 1,
            auto_clicker INTEGER DEFAULT 0,
            fast_recovery INTEGER DEFAULT 1,
            last_auto_click INTEGER,
            last_daily_bonus INTEGER,
            consecutive_days INTEGER DEFAULT 0,
            invited_by INTEGER,
            invite_count INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица достижений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            user_id INTEGER,
            achievement_name TEXT,
            achieved_at INTEGER,
            PRIMARY KEY (user_id, achievement_name)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Функции для работы с базой данных
def get_user_data(user_id):
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'user_id': user[0],
            'username': user[1],
            'chat_id': user[2],
            'score': user[3],
            'coins': user[4],
            'energy': user[5],
            'max_energy': user[6],
            'last_energy_update': user[7],
            'level': user[8],
            'total_clicks': user[9],
            'double_click': user[10],
            'auto_clicker': user[11],
            'fast_recovery': user[12],
            'last_auto_click': user[13],
            'last_daily_bonus': user[14],
            'consecutive_days': user[15],
            'invited_by': user[16],
            'invite_count': user[17]
        }
    return None

def update_user_data(user_data):
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data['user_id'], user_data['username'], user_data['chat_id'],
        user_data['score'], user_data['coins'], user_data['energy'],
        user_data['max_energy'], user_data['last_energy_update'],
        user_data['level'], user_data['total_clicks'], user_data['double_click'],
        user_data['auto_clicker'], user_data['fast_recovery'],
        user_data['last_auto_click'], user_data['last_daily_bonus'],
        user_data['consecutive_days'], user_data['invited_by'],
        user_data['invite_count']
    ))
    conn.commit()
    conn.close()

def create_user_if_not_exists(user_id, username, chat_id):
    user = get_user_data(user_id)
    if not user:
        user_data = {
            'user_id': user_id,
            'username': username,
            'chat_id': chat_id,
            'score': 0,
            'coins': 0,
            'energy': 100,
            'max_energy': 100,
            'last_energy_update': int(time.time()),
            'level': 1,
            'total_clicks': 0,
            'double_click': 1,
            'auto_clicker': 0,
            'fast_recovery': 1,
            'last_auto_click': 0,
            'last_daily_bonus': 0,
            'consecutive_days': 0,
            'invited_by': None,
            'invite_count': 0
        }
        update_user_data(user_data)
        return user_data
    return user

# Функции для обновления энергии
def update_energy(user_data):
    current_time = int(time.time())
    time_diff = current_time - user_data['last_energy_update']
    recovery_rate = user_data['fast_recovery']
    energy_to_add = (time_diff // 60) * recovery_rate
    
    if energy_to_add > 0:
        user_data['energy'] = min(
            user_data['max_energy'],
            user_data['energy'] + energy_to_add
        )
        user_data['last_energy_update'] = current_time - (time_diff % 60)
    
    return user_data

# Функции для проверки достижений
def check_achievements(user_data):
    achievements = []
    
    # Проверка достижений по количеству кликов
    if user_data['total_clicks'] >= 100 and not has_achievement(user_data['user_id'], 'novice'):
        achievements.append('novice')
        add_achievement(user_data['user_id'], 'novice')
    
    if user_data['total_clicks'] >= 1000 and not has_achievement(user_data['user_id'], 'hardworker'):
        achievements.append('hardworker')
        add_achievement(user_data['user_id'], 'hardworker')
    
    # Проверка ежедневного бонуса
    current_time = int(time.time())
    last_bonus = user_data['last_daily_bonus']
    
    if last_bonus == 0 or (current_time - last_bonus) >= 86400:
        yesterday = datetime.now() - timedelta(days=1)
        if last_bonus >= yesterday.timestamp():
            user_data['consecutive_days'] += 1
        else:
            user_data['consecutive_days'] = 1
        
        user_data['last_daily_bonus'] = current_time
        user_data['coins'] += 50
        
        if user_data['consecutive_days'] >= 7 and not has_achievement(user_data['user_id'], 'marathoner'):
            achievements.append('marathoner')
            add_achievement(user_data['user_id'], 'marathoner')
    
    return achievements

def has_achievement(user_id, achievement_name):
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT 1 FROM achievements WHERE user_id = ? AND achievement_name = ?',
        (user_id, achievement_name)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_achievement(user_id, achievement_name):
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO achievements VALUES (?, ?, ?)',
        (user_id, achievement_name, int(time.time()))
    )
    conn.commit()
    conn.close()

# API endpoints для Mini App
@app.route('/api/user/<int:user_id>')
def get_user(user_id):
    user_data = get_user_data(user_id)
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    user_data = update_energy(user_data)
    update_user_data(user_data)
    
    return jsonify({
        'score': user_data['score'],
        'coins': user_data['coins'],
        'energy': user_data['energy'],
        'max_energy': user_data['max_energy'],
        'level': user_data['level'],
        'double_click': user_data['double_click'],
        'auto_clicker': user_data['auto_clicker'],
        'fast_recovery': user_data['fast_recovery']
    })

@app.route('/api/click/<int:user_id>', methods=['POST'])
def handle_click(user_id):
    user_data = get_user_data(user_id)
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    user_data = update_energy(user_data)
    
    if user_data['energy'] <= 0:
        return jsonify({'error': 'No energy'}), 400
    
    # Вычисление награды за клик
    click_reward = user_data['double_click']
    user_data['energy'] -= 1
    user_data['score'] += click_reward
    user_data['coins'] += click_reward
    user_data['total_clicks'] += 1
    
    # Проверка уровня
    new_level = user_data['score'] // 1000 + 1
    if new_level > user_data['level']:
        user_data['level'] = new_level
    
    # Проверка достижений
    achievements = check_achievements(user_data)
    
    update_user_data(user_data)
    
    return jsonify({
        'new_score': user_data['score'],
        'new_energy': user_data['energy'],
        'level_up': new_level > user_data['level'],
        'achievements': achievements
    })

@app.route('/api/shop/<int:user_id>/<item>', methods=['POST'])
def buy_item(user_id, item):
    user_data = get_user_data(user_id)
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    shop_items = {
        'double_click': {'price': 100, 'field': 'double_click', 'value': 2},
        'auto_clicker': {'price': 500, 'field': 'auto_clicker', 'value': 1},
        'max_energy': {'price': 300, 'field': 'max_energy', 'value': 200},
        'fast_recovery': {'price': 400, 'field': 'fast_recovery', 'value': 2}
    }
    
    if item not in shop_items:
        return jsonify({'error': 'Invalid item'}), 400
    
    item_data = shop_items[item]
    
    if user_data['coins'] < item_data['price']:
        return jsonify({'error': 'Not enough coins'}), 400
    
    user_data['coins'] -= item_data['price']
    user_data[item_data['field']] = item_data['value']
    
    update_user_data(user_data)
    
    return jsonify({'success': True, 'new_coins': user_data['coins']})

@app.route('/api/leaderboard')
def get_leaderboard():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, score, level, total_clicks 
        FROM users 
        ORDER BY score DESC 
        LIMIT 100
    ''')
    leaders = cursor.fetchall()
    conn.close()
    
    leaderboard = []
    for i, (username, score, level, total_clicks) in enumerate(leaders, 1):
        leaderboard.append({
            'rank': i,
            'username': username,
            'score': score,
            'level': level,
            'total_clicks': total_clicks
        })
    
    return jsonify(leaderboard)

@app.route('/api/leaderboard/user/<int:user_id>')
def get_user_rank(user_id):
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Получаем рейтинг пользователя
    cursor.execute('''
        SELECT rank FROM (
            SELECT user_id, ROW_NUMBER() OVER (ORDER BY score DESC) as rank
            FROM users
        ) WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    user_rank = result[0] if result else None
    
    # Получаем данные пользователя
    cursor.execute('''
        SELECT username, score, level, total_clicks FROM users WHERE user_id = ?
    ''', (user_id,))
    
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'rank': user_rank,
        'username': user_data[0],
        'score': user_data[1],
        'level': user_data[2],
        'total_clicks': user_data[3]
    })

# HTML страница для Mini App
@app.route('/game/<int:user_id>')
def game_page(user_id):
    return render_template('game.html', user_id=user_id)

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    create_user_if_not_exists(user.id, user.username, chat.id)
    
    keyboard = [
        [InlineKeyboardButton("🎮 Открыть игру", web_app={'url': f"https://yourdomain.com/game/{user.id}"})],
        [InlineKeyboardButton("📊 Таблица лидеров", callback_data="leaderboard"),
         InlineKeyboardButton("🛍️ Магазин", callback_data="shop")],
        [InlineKeyboardButton("👥 Пригласить друзей", callback_data="invite")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Добро пожаловать в Clicker Game! 🎯\n\n"
        "Нажимай на кнопку, зарабатывай очки и улучшай свои способности!",
        reply_markup=reply_markup
    )

async def handle_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start={user.id}"
    
    await update.callback_query.message.reply_text(
        f"Приглашай друзей и получай бонусы! 💎\n\n"
        f"Твоя реферальная ссылка:\n`{invite_link}`\n\n"
        f"За каждого приглашенного друга ты получишь 100 монет!",
        parse_mode='Markdown'
    )

async def handle_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, score, level 
        FROM users 
        ORDER BY score DESC 
        LIMIT 10
    ''')
    leaders = cursor.fetchall()
    conn.close()
    
    leaderboard_text = "🏆 Топ-10 игроков:\n\n"
    for i, (username, score, level) in enumerate(leaders, 1):
        leaderboard_text += f"{i}. {username} - Ур. {level} ({score} очков)\n"
    
    await update.callback_query.message.reply_text(leaderboard_text)

# Система автокликера
async def auto_clicker_system():
    while True:
        try:
            conn = sqlite3.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, auto_clicker, score, coins FROM users WHERE auto_clicker > 0')
            users_with_auto = cursor.fetchall()
            
            for user_id, auto_clicker, score, coins in users_with_auto:
                new_score = score + auto_clicker
                new_coins = coins + auto_clicker
                cursor.execute(
                    'UPDATE users SET score = ?, coins = ? WHERE user_id = ?',
                    (new_score, new_coins, user_id)
                )
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error in auto-clicker system: {e}")
        
        await asyncio.sleep(1)

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

async def main():
    # Запуск Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Инициализация бота
    application = Application.builder().token(TOKEN).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_leaderboard, pattern="^leaderboard$"))
    application.add_handler(CallbackQueryHandler(handle_invite, pattern="^invite$"))
    
    # Запуск системы автокликера
    asyncio.create_task(auto_clicker_system())
    
    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    # Создание папки для шаблонов
    os.makedirs('templates', exist_ok=True)
    
    # Создание HTML шаблона
    with open('templates/game.html', 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Clicker Game</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
        }
        .click-area {
            margin: 30px 0;
            cursor: pointer;
            transition: transform 0.1s;
        }
        .click-area:active {
            transform: scale(0.95);
        }
        .crystal {
            width: 150px;
            height: 150px;
            background: radial-gradient(circle at 30% 30%, #ffd700, #ff6b6b);
            border-radius: 50%;
            margin: 0 auto;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
        }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 20px 0;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        .buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 20px 0;
        }
        button {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            padding: 12px;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            backdrop-filter: blur(10px);
        }
        button:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        .energy-bar {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            margin: 10px 0;
            overflow: hidden;
        }
        .energy-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            transition: width 0.3s;
        }
        .level-badge {
            background: #ff6b6b;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="level-badge">Уровень <span id="level">1</span></div>
        
        <div class="stats">
            <div class="stat-card">
                <div>Очки</div>
                <div id="score">0</div>
            </div>
            <div class="stat-card">
                <div>Монеты</div>
                <div id="coins">0</div>
            </div>
        </div>
        
        <div class="energy-bar">
            <div class="energy-fill" id="energy-fill"></div>
        </div>
        <div>Энергия: <span id="energy">100</span>/<span id="max-energy">100</span></div>
        
        <div class="click-area" onclick="handleClick()">
            <div class="crystal" id="crystal">💎</div>
        </div>
        
        <div class="buttons">
            <button onclick="showShop()">🛍️ Магазин</button>
            <button onclick="showLeaderboard()">📊 Лидеры</button>
        </div>
    </div>

    <script>
        const userId = {{ user_id }};
        let userData = {};
        
        async function loadUserData() {
            try {
                const response = await fetch(`/api/user/${userId}`);
                userData = await response.json();
                updateUI();
            } catch (error) {
                console.error('Error loading user data:', error);
            }
        }
        
        async function handleClick() {
            if (userData.energy <= 0) {
                alert('Недостаточно энергии!');
                return;
            }
            
            try {
                const response = await fetch(`/api/click/${userId}`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.error) {
                    alert(result.error);
                    return;
                }
                
                userData.score = result.new_score;
                userData.energy = result.new_energy;
                
                // Анимация клика
                const crystal = document.getElementById('crystal');
                crystal.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    crystal.style.transform = 'scale(1)';
                }, 100);
                
                // Показ достижений
                if (result.achievements && result.achievements.length > 0) {
                    result.achievements.forEach(achievement => {
                        showAchievement(achievement);
                    });
                }
                
                updateUI();
            } catch (error) {
                console.error('Error handling click:', error);
            }
        }
        
        function updateUI() {
            document.getElementById('score').textContent = userData.score;
            document.getElementById('coins').textContent = userData.coins;
            document.getElementById('energy').textContent = userData.energy;
            document.getElementById('max-energy').textContent = userData.max_energy;
            document.getElementById('level').textContent = userData.level;
            
            const energyPercent = (userData.energy / userData.max_energy) * 100;
            document.getElementById('energy-fill').style.width = energyPercent + '%';
            
            // Изменение внешнего вида кристалла в зависимости от уровня
            const crystal = document.getElementById('crystal');
            if (userData.level >= 10) {
                crystal.style.background = 'radial-gradient(circle at 30% 30%, #00ff88, #0066ff)';
            } else if (userData.level >= 5) {
                crystal.style.background = 'radial-gradient(circle at 30% 30%, #ffd700, #ff8c00)';
            }
        }
        
        function showAchievement(achievement) {
            const messages = {
                'novice': '🎉 Достижение «Новичок»! 100 кликов!',
                'hardworker': '🔥 Достижение «Трудяга»! 1000 кликов!',
                'marathoner': '🏆 Достижение «Марафонец»! 7 дней подряд!'
            };
            
            if (messages[achievement]) {
                alert(messages[achievement]);
            }
        }
        
        async function showShop() {
            const items = [
                {id: 'double_click', name: 'Двойной клик', price: 100, description: '+2 очка за клик'},
                {id: 'auto_clicker', name: 'Автокликер', price: 500, description: '+1 очко в секунду'},
                {id: 'max_energy', name: 'Больше энергии', price: 300, description: 'Макс. энергия 200'},
                {id: 'fast_recovery', name: 'Быстрое восстановление', price: 400, description: '2 энергии/мин'}
            ];
            
            let shopText = '🛍️ Магазин улучшений:\\n\\n';
            items.forEach(item => {
                shopText += `${item.name}\\n${item.description}\\nЦена: ${item.price} монет\\n`;
                shopText += `Купить: /buy_${item.id}\\n\\n`;
            });
            
            alert(shopText);
        }
        
        async function showLeaderboard() {
            try {
                const response = await fetch('/api/leaderboard');
                const leaders = await response.json();
                
                let leaderboardText = '🏆 Топ-10 игроков:\\n\\n';
                leaders.slice(0, 10).forEach(player => {
                    leaderboardText += `${player.rank}. ${player.username}\\n`;
                    leaderboardText += `Ур. ${player.level} | ${player.score} очков\\n\\n`;
                });
                
                alert(leaderboardText);
            } catch (error) {
                console.error('Error loading leaderboard:', error);
            }
        }
        
        // Загрузка данных при старте
        loadUserData();
        // Обновление данных каждые 10 секунд
        setInterval(loadUserData, 10000);
    </script>
</body>
</html>
        ''')
    
    # Запуск приложения
    asyncio.run(main())
