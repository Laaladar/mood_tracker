from flask import Flask, request, jsonify, render_template, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os

app = Flask(__name__)
# Секретный ключ нужен для шифрования сессий (чтобы браузер "помнил" логин)
app.secret_key = 'super-secret-key-123'
DB_NAME = 'mood_tracker.db'

def init_db():
    """Инициализация базы данных: создание таблиц пользователей и логов"""
    with sqlite3.connect(DB_NAME) as conn:
        # 1. Таблица пользователей
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
             login TEXT UNIQUE NOT NULL, 
             password_hash TEXT NOT NULL,
             nickname TEXT, 
             email TEXT, 
             reg_date TEXT)''')
        
        # 2. Таблица записей настроения (связана через user_id)
        conn.execute('''CREATE TABLE IF NOT EXISTS logs 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
             user_id INTEGER, 
             score INTEGER, 
             word TEXT, 
             why TEXT, 
             happy TEXT, 
             date TEXT,
             FOREIGN KEY (user_id) REFERENCES users(id))''')
    print("База данных готова.")

@app.route('/')
def index():
    """Главная страница (теперь Flask ищет её в папке templates)"""
    return render_template('index.html')

# --- ЛОГИКА ПОЛЬЗОВАТЕЛЕЙ ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    login = data['login']
    
    with sqlite3.connect(DB_NAME) as conn:
        user_exists = conn.execute("SELECT id FROM users WHERE login = ?", (login,)).fetchone()
        if user_exists:
            return jsonify({"error": "Этот логин уже занят"}), 400
        
        pw_hash = generate_password_hash(data['password'])
        reg_date = datetime.datetime.now().strftime("%d.%m.%Y")
        
        cur = conn.cursor()
        cur.execute("INSERT INTO users (login, password_hash, nickname, email, reg_date) VALUES (?, ?, ?, ?, ?)",
                    (login, pw_hash, data['nickname'], data['email'], reg_date))
        conn.commit()
        
        # Получаем ID только что созданного пользователя
        new_user_id = cur.lastrowid
        
        # СРАЗУ АВТОРИЗУЕМ: записываем данные в сессию
        session['user_id'] = new_user_id
        session['nickname'] = data['nickname']
        
    return jsonify({"status": "success", "nickname": data['nickname']}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Вход пользователя"""
    data = request.json
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE login = ?", (data['login'],)).fetchone()
        
        # Проверяем: есть ли юзер и совпадает ли пароль с хешем
        if user and check_password_hash(user['password_hash'], data['password']):
            session['user_id'] = user['id']
            session['nickname'] = user['nickname']
            return jsonify({"status": "success", "nickname": user['nickname']})
        
    return jsonify({"error": "Неверный логин или пароль"}), 401

@app.route('/api/logout')
def logout():
    """Выход (очистка сессии)"""
    session.clear()
    return jsonify({"status": "success"})

# --- ЛОГИКА НАСТРОЕНИЯ ---

@app.route('/api/mood', methods=['GET', 'POST'])
def handle_mood():
    """Работа с записями настроения (только для авторизованных)"""
    
    # Проверяем, залогинен ли пользователь через сессию
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Нужно войти в систему"}), 401

    if request.method == 'POST':
        data = request.json
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("INSERT INTO logs (user_id, score, word, why, happy, date) VALUES (?, ?, ?, ?, ?, ?)",
                         (user_id, data['score'], data['word'], data['why'], data['happy'], data['date']))
        return jsonify({"status": "success"}), 201
    
    else: # GET запрос
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM logs WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
            # Возвращаем и список логов, и никнейм из сессии
            return jsonify({
                "logs": [dict(ix) for ix in rows],
                "nickname": session.get('nickname')
            })


if __name__ == '__main__':
    init_db()
    # debug=True автоматически перезагружает сервер при сохранении кода
    app.run(debug=True, port=5000)
