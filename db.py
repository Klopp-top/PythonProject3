from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Настройки подключения к PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/pizza"

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


# Создаем таблицы в базе
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы!")


# Добавляем пользователя в базу
def add_user(telegram_id: int, phone: str, username: str, password: str):
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
            password=password
        )
        session.add(user)
        session.commit()
        print(f"Пользователь {username} добавлен.")
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
        User.password == password
    ).first()
    session.close()
    return user


if __name__ == "__main__":
    init_db()