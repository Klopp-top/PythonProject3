from flask import Flask, request, jsonify
from flask_cors import CORS
import db

app = Flask(__name__)
CORS(app)

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
        return jsonify({"status": "ok", "message": "Регистрация успешна!"})
    else:
        return jsonify({"status": "error", "message": "Пользователь с таким телефоном/логином уже существует"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get("phone")
    password = data.get("password")

    if not all([phone, password]):
        return jsonify({"status": "error", "message": "Введите телефон и пароль"}), 400

    user = db.authenticate_user(phone, password)
    if user:
        return jsonify({
            "status": "ok", 
            "message": "Вход выполнен!",
            "user": {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "phone": user.phone
            }
        })
    else:
        return jsonify({"status": "error", "message": "Неверный телефон или пароль"}), 401

if __name__ == '__main__':
    db.init_db()
    app.run(port=8000)