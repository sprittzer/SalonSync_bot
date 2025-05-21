"""
Модуль системы бронирования для салона красоты.
Обеспечивает управление клиентами, услугами, мастерами и записями.
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db_config import get_db, engine
from models import Base, Client, Service, Master, Schedule, Booking

class BookingSystem:
    """
    Система бронирования для салона красоты.
    
    Обеспечивает:
    - Управление клиентами (добавление, поиск)
    - Управление услугами (список услуг, поиск)
    - Управление мастерами (список мастеров, расписание)
    - Управление записями (создание, отмена, поиск)
    """
    
    def __init__(self):
        """
        Инициализация системы бронирования.
        Создает таблицы в базе данных и заполняет их начальными данными.
        """
        Base.metadata.create_all(bind=engine)
        self._init_services_and_masters()
        logging.info("Booking system initialized")

    def _init_services_and_masters(self) -> None:
        """
        Инициализация базы данных начальными данными.
        
        Создает:
        - Стандартный набор услуг
        - Список мастеров
        - Расписание работы мастеров на 2 недели вперед
        """
        db = next(get_db())
        try:
            # Стандартные услуги
            services = [
                Service(name="Женская стрижка", duration=60, price=1500),
                Service(name="Мужская стрижка", duration=30, price=800),
                Service(name="Окрашивание", duration=120, price=3000),
                Service(name="Маникюр", duration=90, price=2000),
                Service(name="Педикюр", duration=90, price=2500)
            ]
            
            for service in services:
                db.merge(service)
            
            # Мастера
            masters = [
                Master(name="Анна", specialization="Парикмахер"),
                Master(name="Елена", specialization="Колорист"),
                Master(name="Мария", specialization="Мастер маникюра"),
                Master(name="Ирина", specialization="Мастер педикюра")
            ]
            
            for master in masters:
                db.merge(master)
            
            db.commit()
            
            # Стандартное расписание на 2 недели
            masters = db.query(Master).all()
            for master in masters:
                for day in range(14):
                    date = (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")
                    if datetime.strptime(date, "%Y-%m-%d").weekday() < 5:  # Только будни
                        schedule = Schedule(
                            master_id=master.id,
                            date=date,
                            start_time="10:00",
                            end_time="19:00"
                        )
                        db.merge(schedule)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error initializing database: {e}")
            raise
        finally:
            db.close()

    def add_client(self, name: str, phone: str, telegram_id: Optional[int] = None) -> Optional[int]:
        """
        Добавление нового клиента в систему.
        
        Args:
            name: Имя клиента
            phone: Номер телефона
            telegram_id: ID пользователя в Telegram (опционально)
            
        Returns:
            int: ID клиента в базе данных
            None: В случае ошибки
            
        Note:
            Если клиент с таким телефоном или telegram_id уже существует,
            возвращается его ID без создания новой записи.
        """
        db = next(get_db())
        try:
            # Проверяем существование клиента
            existing_client = db.query(Client).filter(
                (Client.phone == phone) | (Client.telegram_id == telegram_id)
            ).first()
            
            if existing_client:
                return existing_client.id
            
            # Создаем нового клиента
            client = Client(name=name, phone=phone, telegram_id=telegram_id)
            db.add(client)
            db.commit()
            return client.id
            
        except IntegrityError:
            db.rollback()
            # Если произошла ошибка уникальности, возвращаем существующего клиента
            client = db.query(Client).filter(Client.phone == phone).first()
            return client.id if client else None
        except Exception as e:
            db.rollback()
            logging.error(f"Error adding client: {e}")
            return None
        finally:
            db.close()

    def get_client_id(self, phone: Optional[str] = None, telegram_id: Optional[int] = None) -> Optional[int]:
        """
        Поиск ID клиента по телефону или telegram_id.
        
        Args:
            phone: Номер телефона для поиска
            telegram_id: ID пользователя в Telegram для поиска
            
        Returns:
            int: ID клиента в базе данных
            None: Если клиент не найден
            
        Note:
            Должен быть указан хотя бы один параметр поиска.
        """
        db = next(get_db())
        try:
            query = db.query(Client)
            if phone:
                client = query.filter(Client.phone == phone).first()
            elif telegram_id:
                client = query.filter(Client.telegram_id == telegram_id).first()
            else:
                return None
            return client.id if client else None
        finally:
            db.close()

    def get_all_services(self) -> List[Dict]:
        """
        Получение списка всех доступных услуг.
        
        Returns:
            List[Dict]: Список услуг с информацией о названии, длительности и цене
        """
        db = next(get_db())
        try:
            services = db.query(Service).all()
            return [
                {
                    'id': s.id,
                    'name': s.name,
                    'duration': s.duration,
                    'price': s.price
                }
                for s in services
            ]
        finally:
            db.close()

    def get_service_by_id(self, service_id: int) -> Optional[Dict]:
        """
        Поиск услуги по ID.
        
        Args:
            service_id: ID услуги для поиска
            
        Returns:
            Dict: Информация об услуге
            None: Если услуга не найдена
        """
        db = next(get_db())
        try:
            service = db.query(Service).filter(Service.id == service_id).first()
            if service:
                return {
                    'id': service.id,
                    'name': service.name,
                    'duration': service.duration,
                    'price': service.price
                }
            return None
        finally:
            db.close()

    def get_all_masters(self) -> List[Dict]:
        """
        Получение списка всех мастеров.
        
        Returns:
            List[Dict]: Список мастеров с информацией о специализации
        """
        db = next(get_db())
        try:
            masters = db.query(Master).all()
            return [
                {
                    'id': m.id,
                    'name': m.name,
                    'specialization': m.specialization
                }
                for m in masters
            ]
        finally:
            db.close()

    def get_masters_for_service(self, service_id: int) -> List[Dict]:
        """
        Получение списка мастеров, выполняющих конкретную услугу.
        
        Args:
            service_id: ID услуги
            
        Returns:
            List[Dict]: Список мастеров, выполняющих услугу
            
        Note:
            В текущей реализации возвращаются все мастера.
            В реальной системе должна быть реализована связь многие-ко-многим
            между мастерами и услугами.
        """
        # В реальной системе здесь должна быть связь многие-ко-многим
        # Для упрощения возвращаем всех мастеров
        return self.get_all_masters()

    def get_available_slots(self, master_id: int, date: str, service_duration: int) -> List[Dict]:
        """
        Получение доступных временных слотов для записи.
        
        Args:
            master_id: ID мастера
            date: Дата в формате YYYY-MM-DD
            service_duration: Продолжительность услуги в минутах
            
        Returns:
            List[Dict]: Список доступных временных слотов
            
        Note:
            Слоты генерируются с шагом 15 минут в рабочее время мастера.
            Учитываются существующие записи и их продолжительность.
        """
        db = next(get_db())
        try:
            # Получаем рабочее время мастера
            schedule = db.query(Schedule).filter(
                Schedule.master_id == master_id,
                Schedule.date == date
            ).first()
            
            if not schedule:
                return []
            
            work_start = datetime.strptime(schedule.start_time, "%H:%M").time()
            work_end = datetime.strptime(schedule.end_time, "%H:%M").time()
            
            # Получаем занятые слоты
            booked_slots = db.query(Booking).filter(
                Booking.master_id == master_id,
                Booking.date == date,
                Booking.status == 'confirmed'
            ).all()
            
            booked_times = [
                (
                    datetime.strptime(b.start_time, "%H:%M").time(),
                    datetime.strptime(b.end_time, "%H:%M").time()
                )
                for b in booked_slots
            ]
            
            # Генерируем доступные слоты
            available_slots = []
            current_time = work_start
            
            while True:
                end_time = (datetime.combine(datetime.today(), current_time) + 
                           timedelta(minutes=service_duration)).time()
                
                if end_time > work_end:
                    break
                
                # Проверяем, не пересекается ли слот с существующими записями
                slot_available = True
                for booked_start, booked_end in booked_times:
                    if not (end_time <= booked_start or current_time >= booked_end):
                        slot_available = False
                        break
                
                if slot_available:
                    available_slots.append({
                        'start_time': current_time.strftime("%H:%M"),
                        'end_time': end_time.strftime("%H:%M")
                    })
                
                # Переходим к следующему слоту с шагом 15 минут
                current_time = (datetime.combine(datetime.today(), current_time) + 
                              timedelta(minutes=15)).time()
            
            return available_slots
        finally:
            db.close()

    def create_booking(self, client_id: int, service_id: int, master_id: int, 
                      date: str, start_time: str) -> bool:
        """
        Создание новой записи на услугу.
        
        Args:
            client_id: ID клиента
            service_id: ID услуги
            master_id: ID мастера
            date: Дата в формате YYYY-MM-DD
            start_time: Время начала в формате HH:MM
            
        Returns:
            bool: True если запись создана успешно, False в случае ошибки
            
        Note:
            Проверяется доступность выбранного времени и создается запись
            с автоматическим расчетом времени окончания услуги.
        """
        db = next(get_db())
        try:
            # Получаем продолжительность услуги
            service = db.query(Service).filter(Service.id == service_id).first()
            if not service:
                return False
            
            end_time = (datetime.strptime(start_time, "%H:%M") + 
                       timedelta(minutes=service.duration)).strftime("%H:%M")
            
            # Проверяем доступность времени
            available_slots = self.get_available_slots(master_id, date, service.duration)
            if not any(slot['start_time'] == start_time for slot in available_slots):
                return False
            
            booking = Booking(
                client_id=client_id,
                service_id=service_id,
                master_id=master_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                status='confirmed'
            )
            
            db.add(booking)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error creating booking: {e}")
            return False
        finally:
            db.close()

    def get_client_bookings(self, client_id: int) -> List[Dict]:
        """
        Получение списка записей клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            List[Dict]: Список записей с информацией об услуге и мастере
        """
        db = next(get_db())
        try:
            bookings = db.query(Booking).filter(
                Booking.client_id == client_id,
                Booking.status == 'confirmed'
            ).all()
            
            return [
                {
                    'id': b.id,
                    'date': b.date,
                    'start_time': b.start_time,
                    'service': b.service.name,
                    'master': b.master.name
                }
                for b in bookings
            ]
        finally:
            db.close()

    def cancel_booking(self, booking_id: int) -> bool:
        """
        Отмена записи.
        
        Args:
            booking_id: ID записи для отмены
            
        Returns:
            bool: True если запись отменена успешно, False в случае ошибки
        """
        db = next(get_db())
        try:
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return False
            
            booking.status = 'cancelled'
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error cancelling booking: {e}")
            return False
        finally:
            db.close()