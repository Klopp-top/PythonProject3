from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Настройки подключения к PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/pizza"
engine = create_engine(DATABASE_URL)


def clear_all_tables():
    with engine.connect() as connection:
        try:
            # Получаем список всех таблиц
            result = connection.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public';"))
            tables = [row[0] for row in result]

            # Очищаем все таблицы
            if tables:
                connection.execute(text(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"))
                print("Все таблицы очищены.")
            else:
                print("Нет таблиц для очистки.")

        except SQLAlchemyError as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    clear_all_tables()