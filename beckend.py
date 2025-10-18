from flask import Flask, request, jsonify
from flask_cors import CORS
from aiogram import Bot, Dispatcher, types, executor
from threading import Thread
import db
import random
import requests

app = Flask(__name__)
CORS(app)

BOT_TOKEN = '7261530454:AAFyfYScsoMSdHyQ2N8nf4oQ0MUMW7GXfAc'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


def send_telegram_message(chat_id, text):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return None


# Telegram bot handlers
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            text="Открыть мини-приложение 🍕",
            web_app=types.WebAppInfo(url="https://python-project3-brown.vercel.app/")
        )
    )
    await message.answer("Привет! Жми кнопку и регистрируйся:", reply_markup=keyboard)


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

    # Генерируем код подтверждения
    verification_code = str(random.randint(100000, 999999))

    success = db.add_user(telegram_id, phone, username, password, verification_code)
    if success:
        # Отправляем код в Telegram
        send_telegram_message(telegram_id, f"🔐 Ваш код подтверждения: {verification_code}")
        return jsonify({"status": "ok", "message": "Код отправлен в Telegram!"})
    else:
        return jsonify({"status": "error", "message": "Ошибка при регистрации"}), 400


@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    telegram_id = data.get("telegram_id")
    code = data.get("code")

    if not all([telegram_id, code]):
        return jsonify({"status": "error", "message": "Введите код"}), 400

    success = db.verify_user_code(telegram_id, code)
    if success:
        return jsonify({"status": "ok", "message": "Регистрация завершена!"})
    else:
        return jsonify({"status": "error", "message": "Неверный код"}), 400


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
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "phone": user.phone
            }
        })
    else:
        return jsonify(
            {"status": "error", "message": "Неверный логин/телефон или пароль, либо аккаунт не подтвержден"}), 401


@app.route('/order', methods=['POST'])
def create_order():
    data = request.json
    user_id = data.get("user_id")
    phone = data.get("phone")
    username = data.get("username")
    items = data.get("items")  # JSON строка
    total_price = data.get("total_price")

    if not all([user_id, phone, username, items, total_price]):
        return jsonify({"status": "error", "message": "Не все данные заказа"}), 400

    order_id = db.add_order(user_id, phone, username, items, total_price)
    if order_id:
        return jsonify({"status": "ok", "message": "Заказ оформлен!", "order_id": order_id})
    else:
        return jsonify({"status": "error", "message": "Ошибка при создании заказа"}), 500


@app.route('/orders', methods=['GET'])
def get_orders():
    orders = db.get_all_orders()
    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order.id,
            "user_id": order.user_id,
            "phone": order.phone,
            "username": order.username,
            "items": order.items,
            "total_price": order.total_price,
            "status": order.status,
            "created_at": order.created_at
        })
    return jsonify({"status": "ok", "orders": orders_list})


@app.route('/order/<int:order_id>/status', methods=['PUT'])
def update_status(order_id):
    data = request.json
    status = data.get("status")

    if not status:
        return jsonify({"status": "error", "message": "Укажите статус"}), 400

    success = db.update_order_status(order_id, status)
    if success:
        return jsonify({"status": "ok", "message": "Статус обновлен"})
    else:
        return jsonify({"status": "error", "message": "Ошибка обновления"}), 500


if __name__ == '__main__':
    db.init_db()


    # Запускаем Telegram бота в отдельном потоке
    def start_bot():
        executor.start_polling(dp, skip_updates=True)


    bot_thread = Thread(target=start_bot)
    bot_thread.start()

    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=8000)