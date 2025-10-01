# backend.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import db

app = Flask(__name__)
CORS(app)  # разрешаем запросы из браузера Telegram WebApp

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    telegram_id = data.get("telegram_id")
    phone = data.get("phone")
    username = data.get("username")
    password = data.get("password")

    if not all([telegram_id, phone, username, password]):
        return jsonify({"status": "error", "message": "Все поля обязательны"}), 400

    success = db.add_user(telegram_id, phone, username, password)
    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "error", "message": "Пользователь уже существует или ошибка БД"}), 500

if __name__ == '__main__':
    db.init_db()
    app.run(port=8000)
