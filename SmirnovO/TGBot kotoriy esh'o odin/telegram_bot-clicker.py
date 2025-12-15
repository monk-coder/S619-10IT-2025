# Telegram Clicker Bot - Backend (Python + Aiogram)
# Требует: pip install aiogram python-dotenv aiohttp asyncpg

import os
import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncpg
from aiohttp import web
import json 
import logging

load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/clicker_bot")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourdomain.com/app")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool: Optional[asyncpg.Pool] = None
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ======================== МОДЕЛИ И КОНСТАНТЫ ========================

UPGRADE_PRICES = {
    "double_click": 100,
    "auto_clicker": 500,
    "more_energy": 300,
    "fast_recovery": 400,
}

ACHIEVEMENTS = {
    "newbie": {"name": "Новичок", "clicks": 100},
    "hardworker": {"name": "Трудяга", "clicks": 1000},
    "daily_clicker": {"name": "Кликер дня", "daily_clicks": 500},
    "marathoner": {"name": "Марафонец", "consecutive_days": 7},
}

# ======================== DATABASE SETUP ========================

async def init_db():
    """Инициализация базы данных"""
    global db_pool
    
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=10, max_size=20)
    
    async with db_pool.acquire() as conn:
        # Таблица пользователей
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                total_clicks BIGINT DEFAULT 0,
                total_coins BIGINT DEFAULT 0,
                level INT DEFAULT 1,
                energy INT DEFAULT 100,
                max_energy INT DEFAULT 100,
                last_energy_recovery TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW(),
                last_activity TIMESTAMP DEFAULT NOW(),
                referrer_id BIGINT,
                referred_count INT DEFAULT 0
            )
        """)
        
        # Таблица апгрейдов
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS upgrades (
                user_id BIGINT PRIMARY KEY,
                double_click INT DEFAULT 0,
                auto_clicker INT DEFAULT 0,
                more_energy INT DEFAULT 0,
                fast_recovery INT DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Таблица достижений
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                achievement_key VARCHAR(255),
                unlocked_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, achievement_key)
            )
        """)
        
        # Таблица лидеров (кэш)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_cache (
                user_id BIGINT PRIMARY KEY,
                rank INT,
                username VARCHAR(255),
                level INT,
                total_clicks BIGINT,
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Таблица ежедневной активности
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_activity (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                date DATE,
                clicks_today INT DEFAULT 0,
                last_activity TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, date)
            )
        """)
        
        # Индексы для оптимизации
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_clicks ON users(total_clicks DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_level ON users(level DESC)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id)")
        
    logger.info("Database initialized successfully")

# ======================== HELPER FUNCTIONS ========================

async def get_or_create_user(user_id: int, user: types.User = None):
    """Получить или создать пользователя"""
    async with db_pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )
        
        if not user_data:
            await conn.execute(
                """
                INSERT INTO users (user_id, username, first_name)
                VALUES ($1, $2, $3)
                """,
                user_id,
                user.username if user else None,
                user.first_name if user else None
            )
            
            await conn.execute(
                "INSERT INTO upgrades (user_id) VALUES ($1)",
                user_id
            )
            
            user_data = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
        
        return user_data

async def update_leaderboard():
    """Обновление кэша таблицы лидеров (запускать раз в час)"""
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM leaderboard_cache")
        
        leaders = await conn.fetch(
            """
            SELECT user_id, username, level, total_clicks,
                   ROW_NUMBER() OVER (ORDER BY total_clicks DESC) as rank
            FROM users
            ORDER BY total_clicks DESC
            LIMIT 100
            """
        )
        
        for idx, leader in enumerate(leaders, 1):
            await conn.execute(
                """
                INSERT INTO leaderboard_cache (user_id, rank, username, level, total_clicks)
                VALUES ($1, $2, $3, $4, $5)
                """,
                leader['user_id'],
                idx,
                leader['username'],
                leader['level'],
                leader['total_clicks']
            )
    
    logger.info("Leaderboard updated")

async def recover_energy(user_id: int):
    """Восстановление энергии с учётом апгрейдов"""
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )
        
        upgrades = await conn.fetchrow(
            "SELECT fast_recovery FROM upgrades WHERE user_id = $1",
            user_id
        )
        
        energy_per_minute = 2 if upgrades['fast_recovery'] > 0 else 1
        
        time_passed = datetime.utcnow() - user['last_energy_recovery']
        minutes_passed = time_passed.total_seconds() / 60
        energy_to_add = int(minutes_passed * energy_per_minute)
        
        new_energy = min(user['energy'] + energy_to_add, user['max_energy'])
        
        await conn.execute(
            """
            UPDATE users 
            SET energy = $1, last_energy_recovery = NOW()
            WHERE user_id = $2
            """,
            new_energy,
            user_id
        )
        
        return new_energy

async def process_click(user_id: int) -> Dict:
    """Обработка клика по кнопке"""
    async with db_pool.acquire() as conn:
        # Восстановление энергии
        energy = await recover_energy(user_id)
        
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )
        
        if user['energy'] < 1:
            return {"success": False, "error": "Энергия закончилась"}
        
        upgrades = await conn.fetchrow(
            "SELECT * FROM upgrades WHERE user_id = $1",
            user_id
        )
        
        # Расчёт очков
        points = 2 if upgrades['double_click'] > 0 else 1
        
        # Обновление
        new_clicks = user['total_clicks'] + points
        new_level = (new_clicks // 1000) + 1
        new_energy = user['energy'] - 1
        
        await conn.execute(
            """
            UPDATE users 
            SET total_clicks = $1, level = $2, energy = $3, last_activity = NOW()
            WHERE user_id = $4
            """,
            new_clicks,
            new_level,
            new_energy,
            user_id
        )
        
        # Обновление ежедневной статистики
        today = datetime.utcnow().date()
        await conn.execute(
            """
            INSERT INTO daily_activity (user_id, date, clicks_today)
            VALUES ($1, $2, 1)
            ON CONFLICT (user_id, date) DO UPDATE
            SET clicks_today = daily_activity.clicks_today + 1
            """,
            user_id,
            today
        )
        
        # Проверка достижений
        await check_achievements(user_id, new_clicks)
        
        return {
            "success": True,
            "clicks": new_clicks,
            "level": new_level,
            "energy": new_energy,
            "points_earned": points
        }

async def auto_click_worker():
    """Автокликер - добавляет +1 очко в секунду для пользователей с апгрейдом"""
    await asyncio.sleep(5)  # Задержка на старт
    
    while True:
        try:
            async with db_pool.acquire() as conn:
                # Получить всех пользователей с автокликером
                users_with_auto = await conn.fetch(
                    """
                    SELECT u.user_id FROM users u
                    JOIN upgrades up ON u.user_id = up.user_id
                    WHERE up.auto_clicker > 0
                    AND u.last_activity > NOW() - INTERVAL '5 minutes'
                    """
                )
                
                for user_row in users_with_auto:
                    user_id = user_row['user_id']
                    
                    user = await conn.fetchrow(
                        "SELECT * FROM users WHERE user_id = $1",
                        user_id
                    )
                    
                    new_clicks = user['total_clicks'] + 1
                    new_level = (new_clicks // 1000) + 1
                    
                    await conn.execute(
                        """
                        UPDATE users 
                        SET total_clicks = $1, level = $2
                        WHERE user_id = $3
                        """,
                        new_clicks,
                        new_level,
                        user_id
                    )
                    
                    await check_achievements(user_id, new_clicks)
        
        except Exception as e:
            logger.error(f"Error in auto_click_worker: {e}")
        
        await asyncio.sleep(1)

async def check_achievements(user_id: int, total_clicks: int):
    """Проверка и разблокировка достижений"""
    async with db_pool.acquire() as conn:
        # Новичок - 100 кликов
        if total_clicks >= 100:
            await unlock_achievement(user_id, "newbie")
        
        # Трудяга - 1000 кликов
        if total_clicks >= 1000:
            await unlock_achievement(user_id, "hardworker")
        
        # Кликер дня - 500 кликов за сутки
        today = datetime.utcnow().date()
        daily_clicks = await conn.fetchval(
            "SELECT COALESCE(clicks_today, 0) FROM daily_activity WHERE user_id = $1 AND date = $2",
            user_id,
            today
        )
        
        if daily_clicks and daily_clicks >= 500:
            await unlock_achievement(user_id, "daily_clicker")
        
        # Марафонец - 7 дней подряд
        consecutive_days = await get_consecutive_days(user_id)
        if consecutive_days >= 7:
            await unlock_achievement(user_id, "marathoner")

async def unlock_achievement(user_id: int, achievement_key: str):
    """Разблокировка достижения"""
    async with db_pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO achievements (user_id, achievement_key)
                VALUES ($1, $2)
                """,
                user_id,
                achievement_key
            )
            
            # Бонус монет за достижение
            await conn.execute(
                "UPDATE users SET total_coins = total_coins + 50 WHERE user_id = $1",
                user_id
            )
        except asyncpg.UniqueViolationError:
            pass  # Достижение уже разблокировано

async def get_consecutive_days(user_id: int) -> int:
    """Получить количество дней активности подряд"""
    async with db_pool.acquire() as conn:
        dates = await conn.fetch(
            """
            SELECT date FROM daily_activity 
            WHERE user_id = $1 
            ORDER BY date DESC 
            LIMIT 30
            """,
            user_id
        )
        
        if not dates:
            return 0
        
        consecutive = 0
        today = datetime.utcnow().date()
        
        for i, row in enumerate(sorted(dates, key=lambda x: x['date'], reverse=True)):
            expected_date = today - timedelta(days=i)
            if row['date'] == expected_date:
                consecutive += 1
            else:
                break
        
        return consecutive

async def generate_referral_link(user_id: int) -> str:
    """Генерация реферальной ссылки"""
    return f"https://t.me/{(await bot.get_me()).username}?start=ref_{user_id}"

# ======================== BOT COMMANDS ========================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    args = message.text.split()
    user_id = message.from_user.id
    
    # Обработка реферальной ссылки
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1][4:])
        
        async with db_pool.acquire() as conn:
            existing = await conn.fetchval(
                "SELECT referrer_id FROM users WHERE user_id = $1",
                user_id
            )
            
            if not existing:
                await conn.execute(
                    """
                    UPDATE users 
                    SET referrer_id = $1
                    WHERE user_id = $2
                    """,
                    referrer_id,
                    user_id
                )
                
                # Бонус реферреру
                await conn.execute(
                    """
                    UPDATE users 
                    SET total_coins = total_coins + 100, referred_count = referred_count + 1
                    WHERE user_id = $1
                    """,
                    referrer_id
                )
    
    await get_or_create_user(user_id, message.from_user)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎮 Открыть игру", web_app=types.WebAppInfo(url=WEBAPP_URL))],
        [types.InlineKeyboardButton(text="📊 Таблица лидеров", callback_data="leaderboard"),
         types.InlineKeyboardButton(text="🏆 Мои достижения", callback_data="achievements")],
        [types.InlineKeyboardButton(text="👥 Мои друзья", callback_data="referrals")]
    ])
    
    await message.answer(
        f"👋 Добро пожаловать в Clicker Game!\n\n"
        f"Кликай, собирай очки, прокачивай улучшения и соревнуйся с друзьями! 🎯",
        reply_markup=keyboard
    )

@dp.message(Command("invite"))
async def cmd_invite(message: types.Message):
    """Команда для получения реферальной ссылки"""
    user_id = message.from_user.id
    await get_or_create_user(user_id, message.from_user)
    
    referral_link = await generate_referral_link(user_id)
    
    async with db_pool.acquire() as conn:
        referred_count = await conn.fetchval(
            "SELECT referred_count FROM users WHERE user_id = $1",
            user_id
        )
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📋 Копировать ссылку", callback_data=f"copy_ref_{user_id}")]
    ])
    
    await message.answer(
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Ваша ссылка:\n<code>{referral_link}</code>\n\n"
        f"Приглашено друзей: <b>{referred_count}</b>\n"
        f"За каждого друга: <b>+100 монет</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "leaderboard")
async def show_leaderboard(query: types.CallbackQuery):
    """Показать таблицу лидеров"""
    async with db_pool.acquire() as conn:
        leaders = await conn.fetch(
            "SELECT rank, username, level, total_clicks FROM leaderboard_cache LIMIT 10"
        )
        
        user_rank = await conn.fetchrow(
            "SELECT rank FROM leaderboard_cache WHERE user_id = $1",
            query.from_user.id
        )
    
    text = "🏆 <b>Топ-10 игроков</b>\n\n"
    
    for leader in leaders:
        medal = "🥇" if leader['rank'] == 1 else "🥈" if leader['rank'] == 2 else "🥉"
        text += f"{medal} #{leader['rank']} {leader['username'] or 'Аноним'} | Уровень: {leader['level']} | Кликов: {leader['total_clicks']}\n"
    
    if user_rank:
        text += f"\n\n👤 <b>Ваше место: #{user_rank['rank']}</b>"
    
    await query.answer()
    await query.message.edit_text(text, parse_mode="HTML")

@dp.callback_query(F.data == "achievements")
async def show_achievements(query: types.CallbackQuery):
    """Показать достижения пользователя"""
    user_id = query.from_user.id
    
    async with db_pool.acquire() as conn:
        achievements = await conn.fetch(
            "SELECT achievement_key FROM achievements WHERE user_id = $1",
            user_id
        )
    
    unlocked_keys = {a['achievement_key'] for a in achievements}
    
    text = "🏆 <b>Ваши достижения</b>\n\n"
    
    for key, info in ACHIEVEMENTS.items():
        if key in unlocked_keys:
            text += f"✅ {info['name']}\n"
        else:
            text += f"❌ {info['name']}\n"
    
    await query.answer()
    await query.message.edit_text(text, parse_mode="HTML")

@dp.callback_query(F.data == "referrals")
async def show_referrals(query: types.CallbackQuery):
    """Показать информацию о рефералах"""
    user_id = query.from_user.id
    
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT referred_count, total_coins FROM users WHERE user_id = $1",
            user_id
        )
    
    text = f"👥 <b>Реферальная программа</b>\n\n" \
           f"Приглашено друзей: <b>{user['referred_count']}</b>\n" \
           f"Заработано монет: <b>{user['referred_count'] * 100}</b>\n\n" \
           f"💰 Ваш баланс: <b>{user['total_coins']}</b>"
    
    await query.answer()
    await query.message.edit_text(text, parse_mode="HTML")

# ======================== WEB APP API ========================

async def handle_get_user(request: web.Request) -> web.Response:
    """API: получить данные пользователя"""
    try:
        user_id = int(request.match_info['user_id'])
        
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            
            upgrades = await conn.fetchrow(
                "SELECT * FROM upgrades WHERE user_id = $1",
                user_id
            )
            
            achievements = await conn.fetch(
                "SELECT achievement_key FROM achievements WHERE user_id = $1",
                user_id
            )
        
        if not user:
            return web.json_response({"error": "User not found"}, status=404)
        
        return web.json_response({
            "user_id": user['user_id'],
            "username": user['username'],
            "total_clicks": user['total_clicks'],
            "total_coins": user['total_coins'],
            "level": user['level'],
            "energy": user['energy'],
            "max_energy": user['max_energy'],
            "upgrades": {
                "double_click": upgrades['double_click'],
                "auto_clicker": upgrades['auto_clicker'],
                "more_energy": upgrades['more_energy'],
                "fast_recovery": upgrades['fast_recovery'],
            },
            "achievements": [a['achievement_key'] for a in achievements]
        })
    
    except Exception as e:
        logger.error(f"Error in handle_get_user: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_click(request: web.Request) -> web.Response:
    """API: обработить клик"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        
        result = await process_click(user_id)
        
        return web.json_response(result)
    
    except Exception as e:
        logger.error(f"Error in handle_click: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_buy_upgrade(request: web.Request) -> web.Response:
    """API: купить апгрейд"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        upgrade_key = data.get("upgrade")
        
        if upgrade_key not in UPGRADE_PRICES:
            return web.json_response({"error": "Invalid upgrade"}, status=400)
        
        price = UPGRADE_PRICES[upgrade_key]
        
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT total_coins FROM users WHERE user_id = $1",
                user_id
            )
            
            if user['total_coins'] < price:
                return web.json_response({"error": "Not enough coins"}, status=400)
            
            # Покупка апгрейда
            await conn.execute(
                f"""
                UPDATE upgrades 
                SET {upgrade_key} = {upgrade_key} + 1
                WHERE user_id = $1
                """,
                user_id
            )
            
            # Вычитание монет
            await conn.execute(
                "UPDATE users SET total_coins = total_coins - $1 WHERE user_id = $2",
                price,
                user_id
            )
            
            # Специальные эффекты для "Больше энергии"
            if upgrade_key == "more_energy":
                await conn.execute(
                    "UPDATE users SET max_energy = max_energy + 100, energy = energy + 100 WHERE user_id = $1",
                    user_id
                )
            
            user = await conn.fetchrow(
                "SELECT total_coins FROM users WHERE user_id = $1",
                user_id
            )
        
        return web.json_response({
            "success": True,
            "coins_left": user['total_coins']
        })
    
    except Exception as e:
        logger.error(f"Error in handle_buy_upgrade: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_get_leaderboard(request: web.Request) -> web.Response:
    """API: получить таблицу лидеров"""
    try:
        async with db_pool.acquire() as conn:
            leaders = await conn.fetch(
                "SELECT rank, username, level, total_clicks FROM leaderboard_cache LIMIT 100"
            )
        
        return web.json_response({
            "leaders": [
                {
                    "rank": leader['rank'],
                    "username": leader['username'] or "Anonymous",
                    "level": leader['level'],
                    "clicks": leader['total_clicks']
                }
                for leader in leaders
            ]
        })
    
    except Exception as e:
        logger.error(f"Error in handle_get_leaderboard: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_recover_energy(request: web.Request) -> web.Response:
    """API: восстановление энергии"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        
        energy = await recover_energy(user_id)
        
        return web.json_response({"energy": energy})
    
    except Exception as e:
        logger.error(f"Error in handle_recover_energy: {e}")
        return web.json_response({"error": str(e)}, status=500)

# ======================== BACKGROUND TASKS ========================

async def background_tasks():
    """Фоновые задачи"""
    # Обновление таблицы лидеров каждый час
    while True:
        try:
            await asyncio.sleep(3600)  # Каждый час
            await update_leaderboard()
        except Exception as e:
            logger.error(f"Error in leaderboard update: {e}")

# ======================== MAIN ========================

async def main():
    """Главная функция"""
    await init_db()
    
    # Запуск Web App сервера
    app = web.Application()
    app.router.add_get('/api/user/{user_id}', handle_get_user)
    app.router.add_post('/api/click', handle_click)
    app.router.add_post('/api/upgrade', handle_buy_upgrade)
    app.router.add_get('/api/leaderboard', handle_get_leaderboard)
    app.router.add_post('/api/recover-energy', handle_recover_energy)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    logger.info("Web server started on http://localhost:8080")
    
    # Запуск асинхронных задач
    asyncio.create_task(background_tasks())
    asyncio.create_task(auto_click_worker())
    
    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
