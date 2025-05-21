"""
Модуль конфигурации базы данных.
Содержит настройки подключения к базе данных и базовые классы SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
from typing import Generator
from sqlalchemy.orm import Session

# Загружаем переменные окружения из .env файла
load_dotenv()

# Конфигурация подключения к базе данных
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'beauty_salon')

# Формируем URL для подключения к базе данных
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем движок SQLAlchemy с настройками пула соединений
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # Максимальное количество постоянных соединений
    max_overflow=10,  # Максимальное количество временных соединений
    pool_timeout=30,  # Таймаут ожидания соединения из пула
    pool_recycle=1800,  # Переподключение каждые 30 минут
)

# Создаем фабрику сессий с настройками
SessionLocal = sessionmaker(
    autocommit=False,  # Отключаем автокоммит
    autoflush=False,  # Отключаем автофлеш
    bind=engine
)

# Базовый класс для всех моделей
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Генератор сессий базы данных.
    
    Yields:
        Session: Сессия базы данных
        
    Example:
        ```python
        for db in get_db():
            # Использование сессии
            result = db.query(Model).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 