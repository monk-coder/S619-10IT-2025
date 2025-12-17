import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from django.conf import settings
from .models import TelegramUser, UserCity
from .keyboards import get_main_keyboard, get_back_keyboard, get_favorite_cities_keyboard, get_yes_no_keyboard

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_weather_from_api(city):
    """Получаем погоду из WeatherAPI (тот же API что и на сайте)"""
    try:
        # Используем тот же API ключ что и в настройках Django
        api_key = getattr(settings, 'WEATHER_API_KEY', '')
        if not api_key:
            logger.error("WEATHER_API_KEY not found in settings")
            return None
            
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&lang=ru"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            weather_data = {
                'city': data['location']['name'],
                'country': data['location']['country'],
                'temperature': data['current']['temp_c'],
                'feels_like': data['current']['feelslike_c'],
                'humidity': data['current']['humidity'],
                'wind_speed': data['current']['wind_kph'] / 3.6,  # конвертируем в м/с
                'description': data['current']['condition']['text'],
                'icon': data['current']['condition']['icon']
            }
            return weather_data
        else:
            logger.error(f"WeatherAPI error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting weather from API: {e}")
        return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    
    # Создаем или получаем пользователя
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
        }
    )
    
    if created:
        logger.info(f"Создан новый пользователь: {telegram_id}")
    
    welcome_text = f"""
👋 Привет, {first_name}! Я бот погодного дашборда.

🌤️ **Я могу:**
• Показывать текущую погоду в любом городе
• Сохранять ваши избранные города  
• Напоминать о ваших задачах с сайта

📋 **Основные команды:**
/weather - Узнать погоду
/favorites - Избранные города  
/tasks - Мои задачи с сайта
/help - Справка

Или используйте кнопки меню ниже 👇
    """
    
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

# Команда /weather
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        city = ' '.join(context.args)
        await send_weather(update, context, city)
    else:
        await update.message.reply_text(
            "🌤️ Введите название города или используйте /weather <город>\n"
            "Например: /weather Москва"
        )

# Обработка текстовых сообщений с городами
async def weather_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    
    # Пропускаем команды меню
    if city in ["🌤️ Погода сейчас", "⭐ Избранные города", "📝 Мои задачи", "ℹ️ Помощь", "🔙 Назад"]:
        return
    
    await send_weather(update, context, city)

async def send_weather(update: Update, context: ContextTypes.DEFAULT_TYPE, city: str):
    try:
        await update.message.reply_chat_action(action='typing')
        
        # Получаем данные о погоде из WeatherAPI
        weather_data = get_weather_from_api(city)
        
        if not weather_data:
            await update.message.reply_text(
                f"❌ Не удалось получить данные для города '{city}'. "
                f"Проверьте название и попробуйте снова."
            )
            return
        
        # Форматируем сообщение
        emoji_map = {
            'ясно': '☀️',
            'солнечно': '☀️',
            'облачно': '⛅', 
            'пасмурно': '☁️',
            'дождь': '🌧️',
            'снег': '❄️',
            'гроза': '⛈️',
            'туман': '🌫️'
        }
        
        condition = weather_data['description'].lower()
        condition_emoji = '🌤️'
        for key, emoji in emoji_map.items():
            if key in condition:
                condition_emoji = emoji
                break
        
        message = f"""
{condition_emoji} **Погода в {weather_data['city']}, {weather_data['country']}**

🌡️ Температура: {weather_data['temperature']}°C
🤔 Ощущается как: {weather_data['feels_like']}°C
💧 Влажность: {weather_data['humidity']}%
💨 Ветер: {weather_data['wind_speed']:.1f} м/с
☁️ {weather_data['description']}
        """
        
        # Сохраняем город в историю пользователя
        telegram_user = TelegramUser.objects.get(telegram_id=update.effective_user.id)
        UserCity.objects.get_or_create(user=telegram_user, city=city)
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        # Предлагаем добавить в избранное
        if not UserCity.objects.filter(user=telegram_user, city=city, is_favorite=True).exists():
            await update.message.reply_text(
                f"Хотите добавить {city} в избранные города для быстрого доступа?",
                reply_markup=get_yes_no_keyboard()
            )
            context.user_data['pending_city'] = city
            
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении данных о погоде.")

# Обработка ответов Да/Нет
async def handle_yes_no_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = update.message.text
    pending_city = context.user_data.get('pending_city')
    
    if pending_city:
        if response == "✅ Да":
            telegram_user = TelegramUser.objects.get(telegram_id=update.effective_user.id)
            user_city, created = UserCity.objects.get_or_create(
                user=telegram_user,
                city=pending_city,
                defaults={'is_favorite': True}
            )
            
            if not user_city.is_favorite:
                user_city.is_favorite = True
                user_city.save()
            
            await update.message.reply_text(
                f"✅ Город {pending_city} добавлен в избранные!",
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "Хорошо, город не добавлен в избранные.",
                reply_markup=get_main_keyboard()
            )
        
        context.user_data.pop('pending_city', None)

# Избранные города
async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = TelegramUser.objects.get(telegram_id=update.effective_user.id)
    favorite_cities = UserCity.objects.filter(user=telegram_user, is_favorite=True)
    
    if not favorite_cities:
        await update.message.reply_text(
            "⭐ У вас пока нет избранных городов.\n"
            "Добавьте город в избранное, чтобы быстро получать погоду."
        )
        return
    
    cities_text = "\n".join([f"• {city.city}" for city in favorite_cities])
    await update.message.reply_text(
        f"⭐ Ваши избранные города:\n\n{cities_text}\n\n"
        f"Нажмите на название города для получения погоды."
    )
    
    # Создаем клавиатуру с избранными городами
    cities = [city.city for city in favorite_cities]
    await update.message.reply_text(
        "Выберите город:",
        reply_markup=get_favorite_cities_keyboard(cities)
    )

# Команда /tasks - интеграция с задачами с сайта
async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = TelegramUser.objects.get(telegram_id=update.effective_user.id)
    
    # Если пользователь привязан к аккаунту на сайте
    if telegram_user.user:
        # Импортируем здесь чтобы избежать циклических импортов
        try:
            from dashboard.models import WeatherTask
            tasks = WeatherTask.objects.filter(user=telegram_user.user)
            
            if tasks:
                tasks_text = "\n".join([f"• **{task.city}**: {task.task_text}" for task in tasks[:5]])
                message = f"📝 **Ваши задачи с сайта:**\n\n{tasks_text}"
                if tasks.count() > 5:
                    message += f"\n\n... и еще {tasks.count() - 5} задач"
            else:
                message = "📝 У вас пока нет задач на сайте."
        except ImportError:
            message = "📝 Функционал задач пока недоступен."
    else:
        message = (
            "📝 Чтобы управлять задачами, привяжите ваш Telegram аккаунт к учетной записи на сайте.\n"
            "Для этого войдите на сайт и в личном кабинете введите код: "
            f"`{telegram_user.telegram_id}`"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_main_keyboard())

# Помощь
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
ℹ️ **Доступные команды:**

/start - Начать работу
/weather <город> - Погода в городе
/favorites - Избранные города  
/tasks - Мои задачи с сайта
/help - Эта справка

**Или используйте кнопки меню:**
🌤️ Погода сейчас - быстрый поиск
⭐ Избранные города - ваши города
📝 Мои задачи - задачи с сайта
    """
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

# Обработка кнопки "Назад"
async def back_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Возвращаемся в главное меню:",
        reply_markup=get_main_keyboard()
    )

# Обработка неизвестных команд
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Неизвестная команда. Используйте /help для списка команд.",
        reply_markup=get_main_keyboard()
    )

# Создание приложения бота
def setup_bot_application():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("favorites", favorites_command))
    application.add_handler(CommandHandler("tasks", tasks_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обработчики текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🌤️ Погода сейчас$"), weather_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^⭐ Избранные города$"), favorites_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📝 Мои задачи$"), tasks_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ℹ️ Помощь$"), help_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🔙 Назад$"), back_command))
    
    # Обработчики Да/Нет
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(✅ Да|❌ Нет)$"), handle_yes_no_response))
    
    # Обработчик погоды (все остальные текстовые сообщения)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, weather_message), group=1)
    
    # Обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    return application