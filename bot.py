"""
Telegram бот для бронирования услуг в салоне красоты.
Обеспечивает интерактивный процесс записи клиентов на услуги.
"""

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from booking_system import BookingSystem
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и системы бронирования
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage())
booking = BookingSystem()

class BookingStates(StatesGroup):
    """
    Состояния FSM для процесса бронирования.
    
    Attributes:
        GET_NAME: Получение имени клиента
        GET_PHONE: Получение телефона клиента
        CHOOSE_SERVICE: Выбор услуги
        CHOOSE_MASTER: Выбор мастера
        CHOOSE_DATE: Выбор даты
        CHOOSE_TIME: Выбор времени
        CONFIRM: Подтверждение бронирования
    """
    GET_NAME = State()
    GET_PHONE = State()
    CHOOSE_SERVICE = State()
    CHOOSE_MASTER = State()
    CHOOSE_DATE = State()
    CHOOSE_TIME = State()
    CONFIRM = State()

def create_service_keyboard(services: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для выбора услуги.
    
    Args:
        services: Список услуг с информацией о названии и длительности
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками услуг
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{s['name']} ({s['duration']} мин)")] 
            for s in services
        ],
        resize_keyboard=True
    )

def create_master_keyboard(masters: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для выбора мастера.
    
    Args:
        masters: Список мастеров
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками мастеров
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=m['name'])] for m in masters],
        resize_keyboard=True
    )

def create_date_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для выбора даты (на 14 дней вперед, только рабочие дни).
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками дат
    """
    today = datetime.now().date()
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=(today + timedelta(days=i)).strftime("%Y-%m-%d"))] 
            for i in range(14) if (today + timedelta(days=i)).weekday() < 5
        ],
        resize_keyboard=True
    )

def create_time_keyboard(slots: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для выбора времени.
    
    Args:
        slots: Список доступных временных слотов
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками времени
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=s['start_time'])] for s in slots],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение с доступными командами.
    """
    await message.answer(
        "👋 Добро пожаловать в салон красоты!\n\n"
        "Доступные команды:\n"
        "📝 /book - Записаться на услугу\n"
        "📋 /my_bookings - Посмотреть ваши записи\n"
        "❌ /cancel - Отменить запись"
    )

@dp.message(Command("book"))
async def cmd_book(message: types.Message, state: FSMContext):
    """
    Начало процесса бронирования.
    Запрашивает имя клиента.
    """
    await state.set_state(BookingStates.GET_NAME)
    await message.answer("👤 Введите ваше имя:")

@dp.message(BookingStates.GET_NAME)
async def process_name(message: types.Message, state: FSMContext):
    """
    Обработка введенного имени.
    Запрашивает телефон клиента.
    """
    await state.update_data(name=message.text.strip())
    await state.set_state(BookingStates.GET_PHONE)
    await message.answer("📱 Введите ваш номер телефона:")

@dp.message(BookingStates.GET_PHONE)
async def process_phone(message: types.Message, state: FSMContext):
    """
    Обработка введенного телефона.
    Проверяет корректность номера и показывает список услуг.
    """
    phone = message.text.strip()
    if not phone.isdigit() or len(phone) < 10:
        await message.answer("❌ Пожалуйста, введите корректный номер телефона (только цифры):")
        return
    
    await state.update_data(phone=phone)
    await state.set_state(BookingStates.CHOOSE_SERVICE)
    
    services = booking.get_all_services()
    keyboard = create_service_keyboard(services)
    await message.answer("💅 Выберите услугу:", reply_markup=keyboard)

@dp.message(BookingStates.CHOOSE_SERVICE)
async def process_service(message: types.Message, state: FSMContext):
    """
    Обработка выбора услуги.
    Показывает список доступных мастеров для выбранной услуги.
    """
    services = booking.get_all_services()
    selected_service = next((s for s in services if s['name'] in message.text), None)
    
    if not selected_service:
        await message.answer("❌ Пожалуйста, выберите услугу из списка:")
        return
    
    await state.update_data(
        service_id=selected_service['id'],
        service_name=selected_service['name'],
        duration=selected_service['duration']
    )
    await state.set_state(BookingStates.CHOOSE_MASTER)
    
    masters = booking.get_masters_for_service(selected_service['id'])
    keyboard = create_master_keyboard(masters)
    await message.answer("💇 Выберите мастера:", reply_markup=keyboard)

@dp.message(BookingStates.CHOOSE_MASTER)
async def process_master(message: types.Message, state: FSMContext):
    """
    Обработка выбора мастера.
    Показывает календарь для выбора даты.
    """
    masters = booking.get_all_masters()
    selected_master = next((m for m in masters if m['name'] == message.text), None)
    
    if not selected_master:
        await message.answer("❌ Пожалуйста, выберите мастера из списка:")
        return
    
    await state.update_data(
        master_id=selected_master['id'],
        master_name=selected_master['name']
    )
    await state.set_state(BookingStates.CHOOSE_DATE)
    
    keyboard = create_date_keyboard()
    await message.answer("📅 Выберите дату:", reply_markup=keyboard)

@dp.message(BookingStates.CHOOSE_DATE)
async def process_date(message: types.Message, state: FSMContext):
    """
    Обработка выбора даты.
    Проверяет доступность даты и показывает доступные временные слоты.
    """
    try:
        selected_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        if selected_date < datetime.now().date():
            raise ValueError("Дата в прошлом")
    except ValueError as e:
        await message.answer("❌ Пожалуйста, выберите корректную дату в формате ГГГГ-ММ-ДД:")
        return
    
    data = await state.get_data()
    slots = booking.get_available_slots(data['master_id'], message.text, data['duration'])
    
    if not slots:
        await message.answer("❌ На эту дату нет свободных слотов. Выберите другую дату:")
        return
    
    await state.update_data(date=message.text)
    await state.set_state(BookingStates.CHOOSE_TIME)
    
    keyboard = create_time_keyboard(slots)
    await message.answer("⏰ Выберите время:", reply_markup=keyboard)

@dp.message(BookingStates.CHOOSE_TIME)
async def process_time(message: types.Message, state: FSMContext):
    """
    Обработка выбора времени.
    Показывает подтверждение бронирования.
    """
    await state.update_data(time=message.text)
    data = await state.get_data()
    
    confirm_text = (
        "📋 Подтвердите запись:\n\n"
        f"🧴 Услуга: {data['service_name']}\n"
        f"💇 Мастер: {data['master_name']}\n"
        f"📅 Дата: {data['date']}\n"
        f"⏰ Время: {data['time']}\n\n"
        "Всё верно?"
    )
    
    await state.set_state(BookingStates.CONFIRM)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
        ],
        resize_keyboard=True
    )
    await message.answer(confirm_text, reply_markup=keyboard)

@dp.message(BookingStates.CONFIRM)
async def process_confirmation(message: types.Message, state: FSMContext):
    """
    Обработка подтверждения бронирования.
    Создает запись в базе данных или отменяет процесс.
    """
    if message.text.lower() not in ['да', '✅ да']:
        await message.answer("❌ Запись отменена.", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    
    data = await state.get_data()
    try:
        client_id = booking.add_client(
            name=data['name'],
            phone=data['phone'],
            telegram_id=message.from_user.id
        )
        if client_id is None:
            logger.error(f"Failed to create client for user {message.from_user.id}")
            await message.answer("❌ Ошибка при создании клиента. Попробуйте снова.", 
                               reply_markup=types.ReplyKeyboardRemove())
            await state.clear()
            return

    except Exception as e:
        logger.error(f"Error adding client: {e}")
        await message.answer("❌ Ошибка при создании клиента. Попробуйте снова.", 
                           reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    
    success = booking.create_booking(
        client_id=client_id,
        service_id=data['service_id'],
        master_id=data['master_id'],
        date=data['date'],
        start_time=data['time']
    )
    
    if success:
        await message.answer(
            "✅ Запись успешно создана!\n\n"
            "Вы можете:\n"
            "📋 Посмотреть ваши записи: /my_bookings\n"
            "❌ Отменить запись: /cancel",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "❌ Ошибка при создании записи. Попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    await state.clear()

@dp.message(Command("my_bookings"))
async def cmd_my_bookings(message: types.Message):
    """
    Показывает список активных записей клиента.
    """
    client_id = booking.get_client_id(telegram_id=message.from_user.id)
    if not client_id:
        await message.answer("📋 У вас нет активных записей.")
        return
    
    bookings = booking.get_client_bookings(client_id)
    if not bookings:
        await message.answer("📋 У вас нет активных записей.")
        return
    
    response = "📋 Ваши записи:\n\n" + "\n\n".join(
        f"📅 {b['date']} в {b['start_time']}\n"
        f"🧴 Услуга: {b['service']}\n"
        f"💇 Мастер: {b['master']}"
        for b in bookings
    )
    await message.answer(response)

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    """
    Начало процесса отмены записи.
    Показывает список записей для отмены.
    """
    client_id = booking.get_client_id(telegram_id=message.from_user.id)
    if not client_id:
        await message.answer("❌ У вас нет записей для отмены.")
        return
    
    bookings = booking.get_client_bookings(client_id)
    if not bookings:
        await message.answer("❌ У вас нет записей для отмены.")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"❌ {b['date']} {b['start_time']} - {b['service']}",
                    callback_data=f"cancel_{b['id']}"
                )
            ] for b in bookings
        ]
    )
    await message.answer("Выберите запись для отмены:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('cancel_'))
async def process_cancel(callback: types.CallbackQuery):
    """
    Обработка отмены записи.
    Удаляет выбранную запись из базы данных.
    """
    booking_id = int(callback.data.split('_')[1])
    if booking.cancel_booking(booking_id):
        await callback.message.edit_text("✅ Запись успешно отменена!")
    else:
        await callback.message.edit_text("❌ Ошибка при отмене записи. Попробуйте позже.")
    await callback.answer()

async def main():
    """
    Основная функция запуска бота.
    """
    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())