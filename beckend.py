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

# Временное хранилище локаций пользователей
user_locations = {}


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


# Временное хранилище локаций пользователей (в продакшене используй Redis)
user_locations = {}


@dp.message_handler(content_types=['location'])
async def handle_location(message: types.Message):
    """Обработка полученной геолокации"""
    user_id = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude

    # Проверяем что это Бухарская область
    # Бухара: широта 39.5-40.3, долгота 63.3-64.9
    is_bukhara = (lat >= 39.5 and lat <= 40.3) and (lon >= 63.3 and lon <= 64.9)

    if not is_bukhara:
        await message.answer(
            "❌ К сожалению, мы не доставляем так далеко.\n\n"
            "Доставка только по Бухарской области.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    text="Вернуться в приложение",
                    web_app=types.WebAppInfo(url="https://python-project3-brown.vercel.app/")
                )
            )
        )
        return

    # Получаем адрес через API
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&accept-language=ru"
            async with session.get(url) as resp:
                data = await resp.json()
                address = data.get('display_name', f'Координаты: {lat}, {lon}')
    except:
        address = f'Координаты: {lat}, {lon}'

    # Сохраняем локацию пользователя
    user_locations[user_id] = {
        'lat': lat,
        'lon': lon,
        'address': address
    }

    await message.answer(
        f"✅ Адрес доставки получен!\n\n📍 {address}\n\n"
        "Теперь вернитесь в приложение и завершите оформление заказа.",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(
                text="Вернуться в приложение",
                web_app=types.WebAppInfo(url="https://python-project3-brown.vercel.app/")
            )
        )
    )


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
    delivery_type = data.get("delivery_type")
    address = data.get("address", "")
    payment_method = data.get("payment_method")

    if not all([user_id, phone, username, items, total_price, delivery_type, payment_method]):
        return jsonify({"status": "error", "message": "Не все данные заказа"}), 400

    order_id = db.add_order(user_id, phone, username, items, total_price,
                            delivery_type, address, payment_method)
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
            "delivery_type": order.delivery_type,
            "address": order.address,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
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


@app.route('/user/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    orders = db.get_user_orders(user_id)
    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order.id,
            "items": order.items,
            "total_price": order.total_price,
            "status": order.status,
            "delivery_type": order.delivery_type,
            "address": order.address,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "created_at": order.created_at
        })
    return jsonify({"status": "ok", "orders": orders_list})


@app.route('/user/<int:user_id>/location', methods=['GET'])
def get_user_location(user_id):
    """Получить сохранённую локацию пользователя"""
    from main import user_locations  # Импортируем из модуля бота

    if user_id in user_locations:
        return jsonify({
            "status": "ok",
            "location": user_locations[user_id]
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Локация не найдена"
        }), 404


if __name__ == '__main__':
    db.init_db()


    # Запускаем Telegram бота в отдельном потоке с новым event loop
    def start_bot():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        executor.start_polling(dp, skip_updates=True)


    bot_thread = Thread(target=start_bot, daemon=True)
    bot_thread.start()

    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=8000)