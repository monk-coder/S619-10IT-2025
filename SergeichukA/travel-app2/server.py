from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import hashlib
import secrets

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
DATABASE = 'travel_app.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None: db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS wishlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                country_name TEXT NOT NULL,
                country_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, country_name)
            )''')
        db.commit()

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path): return send_from_directory('.', path)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username, email, password = data.get('username'), data.get('email'), data.get('password')
    if not all([username, email, password]): return jsonify({'error': 'Все поля обязательны'}), 400
    db = get_db()
    try:
        if db.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone():
            return jsonify({'error': 'Пользователь уже существует'}), 400
        password_hash, api_key = hash_password(password), secrets.token_hex(32)
        cursor = db.execute('INSERT INTO users (username, email, password_hash, api_key) VALUES (?, ?, ?, ?)', 
                          (username, email, password_hash, api_key))
        user_id = cursor.lastrowid
        db.commit()
        return jsonify({'message': 'Регистрация успешна', 'user': {'id': user_id, 'username': username, 'email': email, 'api_key': api_key}}), 201
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if not all([username, password]): return jsonify({'error': 'Все поля обязательны'}), 400
    db = get_db()
    user = db.execute('SELECT id, username, email, password_hash, api_key FROM users WHERE username = ?', (username,)).fetchone()
    if not user or user['password_hash'] != hash_password(password): return jsonify({'error': 'Неверные учетные данные'}), 401
    return jsonify({'message': 'Вход успешен', 'user': {'id': user['id'], 'username': user['username'], 'email': user['email'], 'api_key': user['api_key']}})

@app.route('/api/wishlist', methods=['GET'])
def get_wishlist():
    api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not api_key: return jsonify({'error': 'API ключ обязателен'}), 401
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE api_key = ?', (api_key,)).fetchone()
    if not user: return jsonify({'error': 'Неверный API ключ'}), 401
    wishlist_items = db.execute('SELECT country_data FROM wishlists WHERE user_id = ? ORDER BY created_at DESC', (user['id'],)).fetchall()
    wishlist = [json.loads(item['country_data']) for item in wishlist_items]
    return jsonify({'wishlist': wishlist})

@app.route('/api/wishlist', methods=['POST'])
def add_to_wishlist():
    api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
    country_data = request.json
    if not api_key: return jsonify({'error': 'API ключ обязателен'}), 401
    if not country_data or not country_data.get('name'): return jsonify({'error': 'Данные страны обязательны'}), 400
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE api_key = ?', (api_key,)).fetchone()
    if not user: return jsonify({'error': 'Неверный API ключ'}), 401
    try:
        if db.execute('SELECT id FROM wishlists WHERE user_id = ? AND country_name = ?', (user['id'], country_data['name'])).fetchone():
            return jsonify({'error': 'Страна уже в вишлисте'}), 400
        db.execute('INSERT INTO wishlists (user_id, country_name, country_data) VALUES (?, ?, ?)', 
                  (user['id'], country_data['name'], json.dumps(country_data)))
        db.commit()
        return jsonify({'message': 'Страна добавлена в вишлист'}), 201
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/wishlist/<country_name>', methods=['DELETE'])
def remove_from_wishlist(country_name):
    api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not api_key: return jsonify({'error': 'API ключ обязателен'}), 401
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE api_key = ?', (api_key,)).fetchone()
    if not user: return jsonify({'error': 'Неверный API ключ'}), 401
    try:
        result = db.execute('DELETE FROM wishlists WHERE user_id = ? AND country_name = ?', (user['id'], country_name))
        db.commit()
        return jsonify({'message': 'Страна удалена из вишлиста'}) if result.rowcount > 0 else jsonify({'error': 'Страна не найдена в вишлисте'}), 404
    except Exception as e: return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("Сервер запущен на http://localhost:8000")
    app.run(debug=True, port=8000)