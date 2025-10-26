from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Настройки подключения к PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:123456@localhost:5432/pizza')

# Render использует postgres://, а SQLAlchemy требует postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


# Модель таблицы пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, index=True)
    phone = Column(String, unique=True)
    username = Column(String, unique=True)
    password = Column(String)
    verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)


# Модель таблицы заказов
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    phone = Column(String)
    username = Column(String)
    items = Column(String)  # JSON строка с товарами
    total_price = Column(Integer)
    status = Column(String, default="new")  # new, preparing, ready, delivered
    delivery_type = Column(String)  # pickup, delivery
    address = Column(String, nullable=True)  # Адрес доставки
    payment_method = Column(String)  # cash, card, online
    payment_status = Column(String, default="pending")  # pending, paid
    created_at = Column(String)


# Создаем таблицы в базе
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы!")


# Добавляем пользователя в базу (пока не подтвержден)
def add_user(telegram_id: int, phone: str, username: str, password: str, verification_code: str):
    session = SessionLocal()
    try:
        # Проверяем уникальность телефона и логина
        existing = session.query(User).filter(
            (User.phone == phone) |
            (User.username == username)
        ).first()

        if existing:
            session.close()
            return False

        user = User(
            telegram_id=telegram_id,
            phone=phone,
            username=username,
            password=password,
            verified=False,
            verification_code=verification_code
        )
        session.add(user)
        session.commit()
        print(f"Пользователь {username} добавлен (не подтвержден).")
        return True
    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении пользователя: {e}")
        return False
    finally:
        session.close()


# Поиск пользователя по telegram_id
def get_user_by_telegram_id(telegram_id: int):
    session = SessionLocal()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    session.close()
    return user


# Авторизация пользователя по телефону или логину
def authenticate_user_by_identifier(identifier: str, password: str):
    session = SessionLocal()
    user = session.query(User).filter(
        ((User.phone == identifier) | (User.username == identifier)),
        User.password == password,
        User.verified == True  # Только подтвержденные
    ).first()
    session.close()
    return user

# Проверка и подтверждение кода
def verify_user_code(telegram_id: int, code: str):
    session = SessionLocal()
    user = session.query(User).filter(
        User.telegram_id == telegram_id,
        User.verification_code == code,
        User.verified == False
    ).first()

    if user:
        user.verified = True
        user.verification_code = None
        session.commit()
        session.close()
        return True
    session.close()
    return False

# Получить все заказы
def get_all_orders():
    session = SessionLocal()
    orders = session.query(Order).order_by(Order.id.desc()).all()
    session.close()
    return orders

# Обновить статус заказа
def update_order_status(order_id: int, status: str):
    session = SessionLocal()
    try:
        order = session.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            session.commit()
            session.close()
            return True
        session.close()
        return False
    except Exception as e:
        session.rollback()
        print(f"Ошибка при обновлении статуса: {e}")
        session.close()
        return False


# Получить заказы пользователя
def get_user_orders(user_id: int):
    session = SessionLocal()
    orders = session.query(Order).filter(Order.user_id == user_id).order_by(Order.id.desc()).all()
    session.close()
    return orders


# Добавить заказ
def add_order(user_id: int, phone: str, username: str, items: str, total_price: int,
              delivery_type: str, address: str, payment_method: str):
    session = SessionLocal()
    try:
        from datetime import datetime
        payment_status = "paid" if payment_method == "online" else "pending"

        order = Order(
            user_id=user_id,
            phone=phone,
            username=username,
            items=items,
            total_price=total_price,
            status="new",
            delivery_type=delivery_type,
            address=address,
            payment_method=payment_method,
            payment_status=payment_status,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(order)
        session.commit()
        order_id = order.id
        session.close()
        return order_id
    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении заказа: {e}")
        session.close()
        return None

if __name__ == "__main__":
    init_db()