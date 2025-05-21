"""
Административная панель для управления салоном красоты.
Предоставляет графический интерфейс для управления записями клиентов.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from booking_system import BookingSystem
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdminPanel:
    """
    Графический интерфейс администратора салона красоты.
    
    Предоставляет функционал:
    - Просмотр записей за выбранный период
    - Добавление новых записей
    - Отмена существующих записей
    - Фильтрация по датам (сегодня, завтра, неделя)
    """
    
    def __init__(self):
        """
        Инициализация административной панели.
        Создает главное окно и настраивает интерфейс.
        
        Raises:
            Exception: При ошибке инициализации
        """
        try:
            self.booking = BookingSystem()
            self.window = tk.Tk()
            self.window.title("Beauty Salon Admin Panel")
            self.window.geometry("1000x600")
            self._setup_ui()
            self._load_data()
            logger.info("Admin panel initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize admin panel: {e}")
            messagebox.showerror("Ошибка инициализации", f"Не удалось запустить приложение: {str(e)}")
            self.window.destroy()
            raise

    def _setup_ui(self) -> None:
        """
        Настройка пользовательского интерфейса.
        Создает все необходимые элементы управления и таблицу записей.
        """
        # Основные фреймы
        control_frame = ttk.Frame(self.window, padding="10")
        control_frame.pack(fill=tk.X)

        display_frame = ttk.Frame(self.window)
        display_frame.pack(fill=tk.BOTH, expand=True)

        # Элементы управления
        ttk.Button(control_frame, text="🔄 Обновить", 
                  command=self._load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="➕ Добавить запись", 
                  command=self._add_booking_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="❌ Отменить запись", 
                  command=self._cancel_booking).pack(side=tk.LEFT, padx=5)
        
        # Период отображения
        self.period_var = tk.StringVar(value="today")
        ttk.Radiobutton(control_frame, text="📅 Сегодня", 
                       variable=self.period_var, value="today", 
                       command=self._load_data).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="📅 Завтра", 
                       variable=self.period_var, value="tomorrow", 
                       command=self._load_data).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="📅 Неделя", 
                       variable=self.period_var, value="week", 
                       command=self._load_data).pack(side=tk.LEFT, padx=5)

        # Таблица записей
        columns = ("id", "client", "phone", "service", "master", "date", "time", "duration")
        self.bookings_tree = ttk.Treeview(
            display_frame, columns=columns, show="headings", selectmode="browse"
        )
        
        # Настройка колонок
        column_configs = {
            "id": ("ID", 50, tk.CENTER),
            "client": ("Клиент", 150, tk.W),
            "phone": ("Телефон", 120, tk.W),
            "service": ("Услуга", 150, tk.W),
            "master": ("Мастер", 150, tk.W),
            "date": ("Дата", 100, tk.CENTER),
            "time": ("Время", 80, tk.CENTER),
            "duration": ("Длительность", 100, tk.CENTER)
        }
        
        for col, (text, width, anchor) in column_configs.items():
            self.bookings_tree.heading(col, text=text)
            self.bookings_tree.column(col, width=width, anchor=anchor)

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, 
                                 command=self.bookings_tree.yview)
        self.bookings_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bookings_tree.pack(fill=tk.BOTH, expand=True)

    def _load_data(self) -> None:
        """
        Загрузка и отображение данных в таблице.
        Обновляет таблицу в соответствии с выбранным периодом.
        """
        period = self.period_var.get()
        today = datetime.now().date()
        
        # Определяем период отображения
        if period == "today":
            date_from = today
            date_to = today
        elif period == "tomorrow":
            date_from = today + timedelta(days=1)
            date_to = date_from
        else:  # week
            date_from = today
            date_to = today + timedelta(days=7)
        
        # Очищаем таблицу
        for item in self.bookings_tree.get_children():
            self.bookings_tree.delete(item)
        
        try:
            # Получаем и отображаем записи
            bookings = self._get_bookings_for_period(date_from, date_to)
            for booking in bookings:
                self.bookings_tree.insert("", tk.END, values=(
                    booking['id'],
                    booking['client_name'],
                    booking['client_phone'],
                    booking['service_name'],
                    booking['master_name'],
                    booking['date'],
                    booking['start_time'],
                    f"{booking['duration']} мин"
                ))
            logger.info(f"Loaded {len(bookings)} bookings for period {date_from} - {date_to}")
        except Exception as e:
            logger.error(f"Error loading bookings: {e}")
            messagebox.showerror("Ошибка", "Не удалось загрузить данные")

    def _get_bookings_for_period(self, date_from: datetime.date, 
                               date_to: datetime.date) -> List[Dict[str, Any]]:
        """
        Получение списка записей за указанный период.
        
        Args:
            date_from: Начальная дата периода
            date_to: Конечная дата периода
            
        Returns:
            List[Dict]: Список записей с информацией о клиентах, услугах и мастерах
        """
        all_bookings = []
        current_date = date_from
        
        while current_date <= date_to:
            date_str = current_date.strftime("%Y-%m-%d")
            bookings = self.booking.conn.execute(
                """SELECT b.id, c.name as client_name, c.phone as client_phone,
                          s.name as service_name, m.name as master_name,
                          b.date, b.start_time, s.duration
                   FROM bookings b
                   JOIN clients c ON b.client_id = c.id
                   JOIN services s ON b.service_id = s.id
                   JOIN masters m ON b.master_id = m.id
                   WHERE b.date = ? AND b.status = 'confirmed'
                   ORDER BY b.start_time""",
                (date_str,)
            ).fetchall()
            
            all_bookings.extend([dict(zip(
                ['id', 'client_name', 'client_phone', 'service_name', 
                 'master_name', 'date', 'start_time', 'duration'], row)) 
                for row in bookings])
            
            current_date += timedelta(days=1)
        
        return all_bookings

    def _add_booking_dialog(self) -> None:
        """
        Отображение диалога добавления новой записи.
        Создает окно с формой для ввода данных о записи.
        """
        dialog = tk.Toplevel(self.window)
        dialog.title("➕ Добавить запись")
        dialog.geometry("400x500")
        dialog.transient(self.window)  # Делаем окно модальным
        dialog.grab_set()  # Захватываем фокус
        
        # Переменные для формы
        client_name = tk.StringVar()
        client_phone = tk.StringVar()
        service_var = tk.StringVar()
        master_var = tk.StringVar()
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        time_var = tk.StringVar()
        
        # Заполняем списки услуг и мастеров
        services = [s['name'] for s in self.booking.get_all_services()]
        masters = [m['name'] for m in self.booking.get_all_masters()]
        
        # Создаем и размещаем элементы формы
        form_elements = [
            ("👤 Клиент:", client_name),
            ("📱 Телефон:", client_phone),
            ("💅 Услуга:", service_var, services),
            ("💇 Мастер:", master_var, masters),
            ("📅 Дата (ГГГГ-ММ-ДД):", date_var),
            ("⏰ Время (ЧЧ:ММ):", time_var)
        ]
        
        for label_text, var, *args in form_elements:
            ttk.Label(dialog, text=label_text).pack(pady=(10, 0))
            if args:  # Если есть список значений, создаем Combobox
                ttk.Combobox(dialog, textvariable=var, values=args[0]).pack(
                    fill=tk.X, padx=10, pady=5)
            else:  # Иначе создаем Entry
                ttk.Entry(dialog, textvariable=var).pack(fill=tk.X, padx=10, pady=5)
        
        # Кнопки управления
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="✅ Сохранить", 
                  command=lambda: self._save_booking(
                      client_name.get(),
                      client_phone.get(),
                      service_var.get(),
                      master_var.get(),
                      date_var.get(),
                      time_var.get(),
                      dialog
                  )).pack(side=tk.LEFT, padx=5, expand=True)
        
        ttk.Button(button_frame, text="❌ Отмена", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True)

    def _save_booking(self, client_name: str, client_phone: str, 
                     service_name: str, master_name: str, 
                     date_str: str, time_str: str, dialog: tk.Toplevel) -> None:
        """
        Сохранение новой записи в базу данных.
        
        Args:
            client_name: Имя клиента
            client_phone: Телефон клиента
            service_name: Название услуги
            master_name: Имя мастера
            date_str: Дата в формате YYYY-MM-DD
            time_str: Время в формате HH:MM
            dialog: Окно диалога для закрытия после сохранения
        """
        try:
            # Проверка данных
            if not all([client_name, client_phone, service_name, 
                       master_name, date_str, time_str]):
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения")
                return
            
            # Получаем ID сервиса и мастера
            service_id = next((s['id'] for s in self.booking.get_all_services() 
                             if s['name'] == service_name), None)
            master_id = next((m['id'] for m in self.booking.get_all_masters() 
                            if m['name'] == master_name), None)
            
            if not service_id or not master_id:
                messagebox.showerror("Ошибка", "Услуга или мастер не найдены")
                return
            
            # Проверяем корректность даты и времени
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                datetime.strptime(time_str, "%H:%M")
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты или времени")
                return
            
            # Добавляем клиента или получаем существующего
            client_id = self.booking.add_client(client_name, client_phone)
            if not client_id:
                messagebox.showerror("Ошибка", "Не удалось добавить клиента")
                return
            
            # Создаем запись
            success = self.booking.create_booking(
                client_id=client_id,
                service_id=service_id,
                master_id=master_id,
                date=date_str,
                start_time=time_str
            )
            
            if success:
                logger.info(f"Created new booking for client {client_name}")
                messagebox.showinfo("Успех", "✅ Запись успешно добавлена")
                dialog.destroy()
                self._load_data()
            else:
                messagebox.showerror("Ошибка", "❌ Не удалось создать запись")
                
        except Exception as e:
            logger.error(f"Error saving booking: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

    def _cancel_booking(self) -> None:
        """
        Отмена выбранной записи.
        Запрашивает подтверждение перед отменой.
        """
        selected_item = self.bookings_tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для отмены")
            return
        
        booking_id = self.bookings_tree.item(selected_item)['values'][0]
        booking_info = self.bookings_tree.item(selected_item)['values']
        
        confirm_message = (
            f"Вы уверены, что хотите отменить запись?\n\n"
            f"Клиент: {booking_info[1]}\n"
            f"Услуга: {booking_info[3]}\n"
            f"Дата: {booking_info[5]}\n"
            f"Время: {booking_info[6]}"
        )
        
        if messagebox.askyesno("Подтверждение", confirm_message):
            try:
                success = self.booking.cancel_booking(booking_id)
                if success:
                    logger.info(f"Cancelled booking {booking_id}")
                    messagebox.showinfo("Успех", "✅ Запись отменена")
                    self._load_data()
                else:
                    messagebox.showerror("Ошибка", "❌ Не удалось отменить запись")
            except Exception as e:
                logger.error(f"Error cancelling booking: {e}")
                messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")


def main():
    """
    Точка входа в приложение.
    Запускает административную панель.
    """
    try:
        logger.info("Starting admin panel application")
        app = AdminPanel()
        app.window.mainloop()
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()