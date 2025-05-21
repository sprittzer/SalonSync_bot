"""
Модуль содержит модели данных для системы бронирования салона красоты.
Использует SQLAlchemy ORM для определения структуры базы данных.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from db_config import Base

class Client(Base):
    """
    Модель клиента салона красоты.
    
    Attributes:
        id (int): Уникальный идентификатор клиента
        name (str): Имя клиента
        phone (str): Номер телефона (уникальный)
        telegram_id (int): ID пользователя в Telegram (уникальный)
        bookings (relationship): Связь с бронированиями клиента
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    telegram_id = Column(Integer, unique=True)

    bookings = relationship("Booking", back_populates="client", cascade="all, delete-orphan")

class Service(Base):
    """
    Модель услуги салона красоты.
    
    Attributes:
        id (int): Уникальный идентификатор услуги
        name (str): Название услуги (уникальное)
        duration (int): Продолжительность услуги в минутах
        price (int): Стоимость услуги
        bookings (relationship): Связь с бронированиями услуги
    """
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    duration = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

    bookings = relationship("Booking", back_populates="service", cascade="all, delete-orphan")

class Master(Base):
    """
    Модель мастера салона красоты.
    
    Attributes:
        id (int): Уникальный идентификатор мастера
        name (str): Имя мастера (уникальное)
        specialization (str): Специализация мастера
        bookings (relationship): Связь с бронированиями мастера
        schedule (relationship): Связь с расписанием мастера
    """
    __tablename__ = "masters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    specialization = Column(String)

    bookings = relationship("Booking", back_populates="master", cascade="all, delete-orphan")
    schedule = relationship("Schedule", back_populates="master", cascade="all, delete-orphan")

class Schedule(Base):
    """
    Модель расписания работы мастера.
    
    Attributes:
        id (int): Уникальный идентификатор записи расписания
        master_id (int): ID мастера (внешний ключ)
        date (str): Дата в формате YYYY-MM-DD
        start_time (str): Время начала работы в формате HH:MM
        end_time (str): Время окончания работы в формате HH:MM
        master (relationship): Связь с мастером
    """
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)
    master_id = Column(Integer, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    date = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)

    master = relationship("Master", back_populates="schedule")

class Booking(Base):
    """
    Модель бронирования услуги.
    
    Attributes:
        id (int): Уникальный идентификатор бронирования
        client_id (int): ID клиента (внешний ключ)
        service_id (int): ID услуги (внешний ключ)
        master_id (int): ID мастера (внешний ключ)
        date (str): Дата бронирования в формате YYYY-MM-DD
        start_time (str): Время начала в формате HH:MM
        end_time (str): Время окончания в формате HH:MM
        status (str): Статус бронирования (по умолчанию "confirmed")
        client (relationship): Связь с клиентом
        service (relationship): Связь с услугой
        master (relationship): Связь с мастером
    """
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    master_id = Column(Integer, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False)
    date = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    status = Column(String, default="confirmed")

    client = relationship("Client", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    master = relationship("Master", back_populates="bookings") 