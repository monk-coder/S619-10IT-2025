"""
FastAPI Backend для Weather Dashboard
Простой API сервер для аутентификации и кэширования погодных данных
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import requests
import sqlite3
import hashlib
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from config import OPENWEATHER_API_KEY, SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS, ALLOWED_ORIGINS

load_dotenv()

app = FastAPI(title="Aegis Weather API", version="1.0.0")
api = APIRouter(prefix="/api")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация уже импортирована из config.py

security = HTTPBearer()

# Ensure DB exists on startup
def init_db():
    conn = get_db_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS weather_data (
            city_id INTEGER PRIMARY KEY,
            temperature REAL,
            feels_like REAL,
            humidity INTEGER,
            pressure INTEGER,
            description TEXT,
            icon TEXT,
            wind_speed REAL,
            wind_direction INTEGER,
            visibility INTEGER,
            clouds INTEGER,
            updated_at DATETIME DEFAULT (datetime('now')),
            FOREIGN KEY(city_id) REFERENCES cities(id)
        );

        CREATE TRIGGER IF NOT EXISTS trg_weather_updated
        AFTER INSERT ON weather_data
        BEGIN
            UPDATE weather_data SET updated_at = datetime('now') WHERE city_id = NEW.city_id;
        END;

        CREATE TABLE IF NOT EXISTS weather_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            city_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            completed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(city_id) REFERENCES cities(id)
        );

        CREATE TABLE IF NOT EXISTS search_history (
            user_id INTEGER NOT NULL,
            city_id INTEGER NOT NULL,
            searched_at DATETIME DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, city_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(city_id) REFERENCES cities(id)
        );
        """
    )
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('weather_dashboard.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_jwt_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, email FROM users WHERE id = ?", (payload["user_id"],)
    ).fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    return {"id": user["id"], "email": user["email"]}

# API endpoints
@app.get("/")
async def root():
    return {"message": "Weather Dashboard API", "version": "1.0.0"}

@api.post("/auth/register/", response_model=dict)
async def register(user_data: UserRegister):
    conn = get_db_connection()
    
    # Проверка существования пользователя
    existing_user = conn.execute(
        "SELECT id FROM users WHERE email = ?", (user_data.email,)
    ).fetchone()
    
    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    # Создание пользователя
    password_hash = hash_password(user_data.password)
    cursor = conn.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (user_data.email, password_hash)
    )
    user_id = cursor.lastrowid
    
    # Создание профиля
    conn.execute(
        "INSERT INTO user_profiles (user_id) VALUES (?)",
        (user_id,)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Пользователь успешно зарегистрирован"}

@api.post("/auth/login/", response_model=dict)
async def login(user_data: UserLogin):
    conn = get_db_connection()
    
    user = conn.execute(
        "SELECT id, email, password_hash FROM users WHERE email = ?",
        (user_data.email,)
    ).fetchone()
    
    if not user or not verify_password(user_data.password, user["password_hash"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    
    token = create_jwt_token(user["id"], user["email"])
    conn.close()
    
    return {
        "success": True,
        "token": token,
        "user": {"id": user["id"], "email": user["email"]}
    }

@api.get("/weather/{city_name}/", response_model=WeatherResponse)
async def get_weather_public(city_name: str):
    """Публичный endpoint для получения погоды без аутентификации"""
    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "":
        raise HTTPException(status_code=500, detail="API ключ не настроен")
    
    conn = get_db_connection()
    
    # Поиск города в базе
    city = conn.execute(
        "SELECT id FROM cities WHERE name = ?", (city_name.title(),)
    ).fetchone()
    
    if not city:
        # Добавление нового города
        cursor = conn.execute(
            "INSERT INTO cities (name) VALUES (?)", (city_name.title(),)
        )
        city_id = cursor.lastrowid
    else:
        city_id = city["id"]
    
    # Проверка кэша (данные не старше 2 часов)
    cached_weather = conn.execute("""
        SELECT * FROM weather_data 
        WHERE city_id = ? AND updated_at > datetime('now', '-2 hours')
        ORDER BY updated_at DESC LIMIT 1
    """, (city_id,)).fetchone()
    
    if cached_weather:
        conn.close()
        payload = dict(cached_weather)
        response_data = {
            "city": {"name": city_name.title()},
            "temperature": payload.get("temperature"),
            "feels_like": payload.get("feels_like"),
            "humidity": payload.get("humidity"),
            "pressure": payload.get("pressure"),
            "description": payload.get("description"),
            "icon": payload.get("icon"),
            "wind_speed": payload.get("wind_speed"),
            "wind_direction": payload.get("wind_direction"),
            "visibility": payload.get("visibility"),
            "clouds": payload.get("clouds"),
        }
        return WeatherResponse(success=True, data=response_data, cached=True)
    
    # Запрос к OpenWeatherMap API
    try:
        response = requests.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city_name,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "ru"
            },
            timeout=10
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Город не найден")
        
        response.raise_for_status()
        data = response.json()
        
        # Сохранение в базу
        weather_data = {
            "city_id": city_id,
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "wind_speed": data.get("wind", {}).get("speed", 0),
            "wind_direction": data.get("wind", {}).get("deg", 0),
            "visibility": data.get("visibility", 0),
            "clouds": data.get("clouds", {}).get("all", 0),
        }
        
        conn.execute("""
            INSERT OR REPLACE INTO weather_data 
            (city_id, temperature, feels_like, humidity, pressure, description, 
             icon, wind_speed, wind_direction, visibility, clouds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(weather_data.values()))
        
        conn.commit()
        conn.close()
        
        response_data = {"city": {"name": city_name.title()}, **weather_data}
        return WeatherResponse(success=True, data=response_data, cached=False)
        
    except requests.RequestException as e:
        conn.close()
        raise HTTPException(status_code=503, detail="Ошибка при получении данных о погоде")

@api.get("/weather-auth/{city_name}/", response_model=WeatherResponse)
async def get_weather_auth(city_name: str, current_user: dict = Depends(get_current_user)):
    
    conn = get_db_connection()
    
    # Поиск города в базе
    city = conn.execute(
        "SELECT id FROM cities WHERE name = ?", (city_name.title(),)
    ).fetchone()
    
    if not city:
        # Добавление нового города
        cursor = conn.execute(
            "INSERT INTO cities (name) VALUES (?)", (city_name.title(),)
        )
        city_id = cursor.lastrowid
    else:
        city_id = city["id"]
    
    # Проверка кэша (данные не старше 2 часов)
    cached_weather = conn.execute("""
        SELECT * FROM weather_data 
        WHERE city_id = ? AND updated_at > datetime('now', '-2 hours')
        ORDER BY updated_at DESC LIMIT 1
    """, (city_id,)).fetchone()
    
    if cached_weather:
        conn.close()
        payload = dict(cached_weather)
        response_data = {
            "city": {"name": city_name.title()},
            "temperature": payload.get("temperature"),
            "feels_like": payload.get("feels_like"),
            "humidity": payload.get("humidity"),
            "pressure": payload.get("pressure"),
            "description": payload.get("description"),
            "icon": payload.get("icon"),
            "wind_speed": payload.get("wind_speed"),
            "wind_direction": payload.get("wind_direction"),
            "visibility": payload.get("visibility"),
            "clouds": payload.get("clouds"),
        }
        return WeatherResponse(success=True, data=response_data, cached=True)
    
    # Запрос к OpenWeatherMap API
    try:
        response = requests.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city_name,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "ru"
            },
            timeout=10
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Город не найден")
        
        response.raise_for_status()
        data = response.json()
        
        # Сохранение в базу
        weather_data = {
            "city_id": city_id,
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "wind_speed": data.get("wind", {}).get("speed", 0),
            "wind_direction": data.get("wind", {}).get("deg", 0),
            "visibility": data.get("visibility", 0),
            "clouds": data.get("clouds", {}).get("all", 0),
        }
        
        conn.execute("""
            INSERT OR REPLACE INTO weather_data 
            (city_id, temperature, feels_like, humidity, pressure, description, 
             icon, wind_speed, wind_direction, visibility, clouds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(weather_data.values()))
        
        # Добавление в историю поиска
        conn.execute("""
            INSERT OR REPLACE INTO search_history (user_id, city_id)
            VALUES (?, ?)
        """, (current_user["id"], city_id))
        
        conn.commit()
        conn.close()
        
        response_data = {"city": {"name": city_name.title()}, **weather_data}
        return WeatherResponse(success=True, data=response_data, cached=False)
        
    except requests.RequestException as e:
        conn.close()
        raise HTTPException(status_code=503, detail="Ошибка при получении данных о погоде")

@api.get("/tasks/", response_model=List[TaskResponse])
async def get_tasks(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    
    tasks = conn.execute("""
        SELECT wt.*, c.name as city_name
        FROM weather_tasks wt
        LEFT JOIN cities c ON wt.city_id = c.id
        WHERE wt.user_id = ?
        ORDER BY wt.created_at DESC
    """, (current_user["id"],)).fetchall()
    
    conn.close()
    
    return [
        TaskResponse(
            id=task["id"],
            title=task["title"],
            description=task["description"],
            city=task["city_name"] or "Неизвестно",
            priority=task["priority"],
            completed=bool(task["completed"]),
            created_at=task["created_at"]
        )
        for task in tasks
    ]

@api.post("/tasks/", response_model=TaskResponse)
async def create_task(task_data: TaskCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    
    # Поиск или создание города
    city = conn.execute(
        "SELECT id FROM cities WHERE name = ?", (task_data.city,)
    ).fetchone()
    
    if not city:
        cursor = conn.execute(
            "INSERT INTO cities (name) VALUES (?)", (task_data.city,)
        )
        city_id = cursor.lastrowid
    else:
        city_id = city["id"]
    
    # Создание задачи
    cursor = conn.execute("""
        INSERT INTO weather_tasks (user_id, city_id, title, description, priority)
        VALUES (?, ?, ?, ?, ?)
    """, (current_user["id"], city_id, task_data.title, task_data.description, task_data.priority))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return TaskResponse(
        id=task_id,
        title=task_data.title,
        description=task_data.description,
        city=task_data.city,
        priority=task_data.priority,
        completed=False,
        created_at=datetime.now().isoformat()
    )

@api.get("/history/", response_model=List[dict])
async def get_search_history(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    
    history = conn.execute("""
        SELECT c.name as city_name, sh.searched_at
        FROM search_history sh
        JOIN cities c ON sh.city_id = c.id
        WHERE sh.user_id = ?
        ORDER BY sh.searched_at DESC
        LIMIT 10
    """, (current_user["id"],)).fetchall()
    
    conn.close()
    
    return [dict(item) for item in history]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Mount the API router
app.include_router(api)
