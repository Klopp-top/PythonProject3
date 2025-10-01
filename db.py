from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Настройки подключения к PostgreSQL — замени пароль и хост, если нужно
DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/pizza"

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Модель таблицы пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    phone = Column(String, unique=True)
    username = Column(String, unique=True)
    password = Column(String)  # В реальном проекте — хэшируй пароль!

# Создаем таблицы в базе
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы!")

# Добавляем пользователя в базу
def add_user(telegram_id: int, phone: str, username: str, password: str):
    session = SessionLocal()
    try:
        user = User(
            telegram_id=telegram_id,
            phone=phone,
            username=username,
            password=password
        )
        session.add(user)
        session.commit()
        print(f"Пользователь {username} добавлен.")
    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении пользователя: {e}")
    finally:
        session.close()

# Поиск пользователя по telegram_id
def get_user_by_telegram_id(telegram_id: int):
    session = SessionLocal()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    session.close()
    return user

if __name__ == "__main__":
    init_db()

    # Пример добавления тестового пользователя
    add_user(telegram_id=123456789, phone="79991234567", username="testuser", password="1234")

    # Проверка
    user = get_user_by_telegram_id(123456789)
    if user:
        print(f"Найден пользователь: {user.username}, телефон: {user.phone}")
    else:
        print("Пользователь не найден.")
