from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем URL БД из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Проверяем, что URL загружен
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

# Создаем движок SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Размер пула соединений
    max_overflow=20,        # Макс. доп. соединений
    pool_pre_ping=True,     # Проверка соединения перед использованием
    echo=True               # Логирование SQL (отключите в продакшене!)
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Базовый класс для моделей
Base = declarative_base()

# Dependency для получения сессии БД
def get_db():
    """
    Генератор сессии БД для использования в зависимостях FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()