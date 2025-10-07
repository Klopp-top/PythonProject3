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

    # Проверяем существование телефона
    existing_phone = db.SessionLocal().query(db.User).filter(db.User.phone == phone).first()
    if existing_phone:
        return jsonify({"status": "error", "message": "Этот номер телефона уже зарегистрирован"}), 400

    # Проверяем существование логина
    existing_username = db.SessionLocal().query(db.User).filter(db.User.username == username).first()
    if existing_username:
        return jsonify({"status": "error", "message": "Этот логин уже занят"}), 400

    success = db.add_user(telegram_id, phone, username, password)
    if success:
        return jsonify({"status": "ok", "message": "Регистрация успешна!"})
    else:
        return jsonify({"status": "error", "message": "Ошибка при регистрации"}), 400


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    identifier = data.get("identifier")  # Логин или телефон
    password = data.get("password")

    if not all([identifier, password]):
        return jsonify({"status": "error", "message": "Введите логин/телефон и пароль"}), 400

    user = db.authenticate_user_by_identifier(identifier, password)
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
        return jsonify({"status": "error", "message": "Неверный логин/телефон или пароль"}), 401


if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=8000)