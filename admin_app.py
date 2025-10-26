import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
from datetime import datetime
import threading
import time


class PizzaAdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍕 Админ-панель пиццерии")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")

        # API URL
        self.API_URL = "http://localhost:8000"

        # Создаем интерфейс
        self.create_widgets()

        # Автообновление
        self.auto_refresh = True
        self.refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        self.refresh_thread.start()

    def create_widgets(self):
        # Заголовок
        header_frame = tk.Frame(self.root, bg="#11998e", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🍕 Панель управления заказами",
            font=("Arial", 24, "bold"),
            bg="#11998e",
            fg="white"
        )
        title_label.pack(pady=20)

        # Панель статистики
        stats_frame = tk.Frame(self.root, bg="#f0f0f0")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        # Карточки статистики
        self.total_orders_label = self.create_stat_card(stats_frame, "Всего заказов", "0", 0)
        self.new_orders_label = self.create_stat_card(stats_frame, "Новые", "0", 1)
        self.preparing_label = self.create_stat_card(stats_frame, "Готовятся", "0", 2)
        self.revenue_label = self.create_stat_card(stats_frame, "Выручка сегодня", "0 сум", 3)

        # Панель управления
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, padx=20, pady=5)

        refresh_btn = tk.Button(
            control_frame,
            text="🔄 Обновить",
            command=self.load_orders,
            bg="#11998e",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        filter_label = tk.Label(control_frame, text="Фильтр:", bg="#f0f0f0", font=("Arial", 11))
        filter_label.pack(side=tk.LEFT, padx=(20, 5))

        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(
            control_frame,
            textvariable=self.filter_var,
            values=["all", "new", "preparing", "ready", "delivered"],
            state="readonly",
            width=15
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.load_orders())

        # Список заказов
        orders_frame = tk.Frame(self.root, bg="white")
        orders_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Scrollbar
        scrollbar = tk.Scrollbar(orders_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.orders_canvas = tk.Canvas(
            orders_frame,
            bg="white",
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        self.orders_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.orders_canvas.yview)

        self.orders_inner_frame = tk.Frame(self.orders_canvas, bg="white")
        self.canvas_frame = self.orders_canvas.create_window(
            (0, 0),
            window=self.orders_inner_frame,
            anchor="nw"
        )

        # Обновляем размер скролла
        self.orders_inner_frame.bind(
            "<Configure>",
            lambda e: self.orders_canvas.configure(scrollregion=self.orders_canvas.bbox("all"))
        )

        # Статус бар
        status_frame = tk.Frame(self.root, bg="#11998e", height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            status_frame,
            text="Готово к работе",
            bg="#11998e",
            fg="white",
            font=("Arial", 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Первая загрузка
        self.load_orders()

    def create_stat_card(self, parent, title, value, column):
        card = tk.Frame(parent, bg="white", relief=tk.RAISED, bd=2)
        card.grid(row=0, column=column, padx=10, sticky="ew")
        parent.grid_columnconfigure(column, weight=1)

        title_label = tk.Label(
            card,
            text=title,
            bg="white",
            fg="#666",
            font=("Arial", 10)
        )
        title_label.pack(pady=(10, 5))

        value_label = tk.Label(
            card,
            text=value,
            bg="white",
            fg="#11998e",
            font=("Arial", 20, "bold")
        )
        value_label.pack(pady=(0, 10))

        return value_label

    def load_orders(self):
        # Запускаем загрузку в отдельном потоке чтобы не блокировать UI
        threading.Thread(target=self._load_orders_thread, daemon=True).start()

    def _load_orders_thread(self):
        try:
            self.root.after(0, lambda: self.status_label.config(text="Загрузка заказов..."))
            response = requests.get(f"{self.API_URL}/orders", timeout=5)
            data = response.json()

            if data["status"] == "ok":
                orders = data["orders"]

                # Применяем фильтр
                filter_status = self.filter_var.get()
                if filter_status != "all":
                    orders = [o for o in orders if o["status"] == filter_status]

                # Обновляем UI в главном потоке
                self.root.after(0, lambda: self.render_orders(orders))
                self.root.after(0, lambda: self.update_stats(data["orders"]))
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Обновлено: {datetime.now().strftime('%H:%M:%S')}"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось загрузить заказы"))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"Ошибка: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Ошибка подключения",
                                                            f"Не удалось подключиться к серверу:\n{str(e)}"))

    def render_orders(self, orders):
        # Очищаем предыдущие заказы
        for widget in self.orders_inner_frame.winfo_children():
            widget.destroy()

        if not orders:
            no_orders = tk.Label(
                self.orders_inner_frame,
                text="Нет заказов",
                bg="white",
                fg="#999",
                font=("Arial", 14)
            )
            no_orders.pack(pady=50)
            return

        # Отрисовываем каждый заказ
        for order in orders:
            self.create_order_card(order)

    def create_order_card(self, order):
        # Цвета для статусов
        status_colors = {
            "new": "#11998e",
            "preparing": "#ffa726",
            "ready": "#66bb6a",
            "delivered": "#9e9e9e"
        }
        status_names = {
            "new": "Новый",
            "preparing": "Готовится",
            "ready": "Готов",
            "delivered": "Доставлен"
        }

        color = status_colors.get(order["status"], "#11998e")

        # Карточка заказа
        card = tk.Frame(
            self.orders_inner_frame,
            bg="white",
            relief=tk.SOLID,
            bd=2,
            highlightbackground=color,
            highlightthickness=3
        )
        card.pack(fill=tk.X, padx=10, pady=5)

        # Заголовок заказа
        header = tk.Frame(card, bg=color, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        order_title = tk.Label(
            header,
            text=f"Заказ #{order['id']} - {status_names[order['status']]}",
            bg=color,
            fg="white",
            font=("Arial", 14, "bold")
        )
        order_title.pack(side=tk.LEFT, padx=15, pady=10)

        order_time = tk.Label(
            header,
            text=order["created_at"],
            bg=color,
            fg="white",
            font=("Arial", 10)
        )
        order_time.pack(side=tk.RIGHT, padx=15, pady=10)

        # Контент заказа
        content = tk.Frame(card, bg="white")
        content.pack(fill=tk.BOTH, padx=15, pady=10)

        # Информация о клиенте
        client_frame = tk.Frame(content, bg="white")
        client_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            client_frame,
            text=f"👤 Клиент: {order['username']}",
            bg="white",
            font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(
            client_frame,
            text=f"📱 Телефон: {order['phone']}",
            bg="white",
            font=("Arial", 11)
        ).pack(side=tk.LEFT)

        # Тип доставки и адрес
        delivery_frame = tk.Frame(content, bg="white")
        delivery_frame.pack(fill=tk.X, pady=5)

        delivery_type_text = "🏪 Самовывоз" if order.get('delivery_type') == 'pickup' else "🚚 Доставка"
        delivery_icon = "🏪" if order.get('delivery_type') == 'pickup' else "🚚"

        delivery_label = tk.Label(
            delivery_frame,
            text=f"{delivery_icon} {delivery_type_text}",
            bg="white",
            font=("Arial", 11, "bold"),
            fg="#1a5f1a"
        )
        delivery_label.pack(side=tk.LEFT)

        # Показываем адрес если доставка
        if order.get('delivery_type') == 'delivery' and order.get('address'):
            address_label = tk.Label(
                delivery_frame,
                text=f"📍 {order['address']}",
                bg="white",
                font=("Arial", 10),
                fg="#666"
            )
            address_label.pack(side=tk.LEFT, padx=(10, 0))

        # Способ оплаты
        payment_frame = tk.Frame(content, bg="white")
        payment_frame.pack(fill=tk.X, pady=5)

        payment_icons = {
            'cash': '💵',
            'card': '💳',
            'online': '🌐'
        }
        payment_names = {
            'cash': 'Наличными при получении',
            'card': 'Картой при получении',
            'online': 'Оплачено онлайн'
        }

        payment_icon = payment_icons.get(order.get('payment_method'), '💵')
        payment_name = payment_names.get(order.get('payment_method'), 'Наличными')

        tk.Label(
            payment_frame,
            text=f"{payment_icon} {payment_name}",
            bg="white",
            font=("Arial", 11, "bold"),
            fg="#1a5f1a"
        ).pack(side=tk.LEFT)

        # Статус оплаты
        if order.get('payment_status') == 'paid':
            paid_badge = tk.Label(
                payment_frame,
                text="✓ Оплачено",
                bg="#66bb6a",
                fg="white",
                font=("Arial", 9, "bold"),
                padx=8,
                pady=3
            )
            paid_badge.pack(side=tk.LEFT, padx=10)
        else:
            unpaid_badge = tk.Label(
                payment_frame,
                text="Ожидает оплаты",
                bg="#ffa726",
                fg="white",
                font=("Arial", 9, "bold"),
                padx=8,
                pady=3
            )
            unpaid_badge.pack(side=tk.LEFT, padx=10)

        # Товары
        items_frame = tk.Frame(content, bg="white")
        items_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            items_frame,
            text="Товары:",
            bg="white",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        items = json.loads(order["items"])
        for item in items:
            item_text = f"  • {item['name']} x{item['quantity']} — {(item['price'] * item['quantity']):,} сум"
            tk.Label(
                items_frame,
                text=item_text,
                bg="white",
                font=("Arial", 10)
            ).pack(anchor="w", pady=2)

        # Итого и управление
        bottom_frame = tk.Frame(content, bg="white")
        bottom_frame.pack(fill=tk.X, pady=10)

        total_label = tk.Label(
            bottom_frame,
            text=f"Итого: {order['total_price']:,} сум",
            bg="white",
            fg=color,
            font=("Arial", 16, "bold")
        )
        total_label.pack(side=tk.LEFT)

        # Кнопки смены статуса
        status_frame = tk.Frame(bottom_frame, bg="white")
        status_frame.pack(side=tk.RIGHT)

        statuses = [
            ("Новый", "new"),
            ("Готовится", "preparing"),
            ("Готов", "ready"),
            ("Доставлен", "delivered")
        ]

        for status_name, status_value in statuses:
            if status_value != order["status"]:
                btn = tk.Button(
                    status_frame,
                    text=status_name,
                    command=lambda oid=order['id'], s=status_value: self.update_status(oid, s),
                    bg=status_colors[status_value],
                    fg="white",
                    font=("Arial", 9, "bold"),
                    relief=tk.FLAT,
                    padx=10,
                    pady=5,
                    cursor="hand2"
                )
                btn.pack(side=tk.LEFT, padx=3)

    def update_status(self, order_id, status):
        # Запускаем в отдельном потоке
        threading.Thread(target=self._update_status_thread, args=(order_id, status), daemon=True).start()

    def _update_status_thread(self, order_id, status):
        try:
            response = requests.put(
                f"{self.API_URL}/order/{order_id}/status",
                json={"status": status},
                timeout=5
            )
            data = response.json()

            if data["status"] == "ok":
                self.root.after(0, lambda: self.load_orders())
                self.root.after(0, lambda: messagebox.showinfo("Успех", f"Статус заказа #{order_id} обновлен!"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось обновить статус"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка подключения:\n{str(e)}"))

    def update_stats(self, orders):
        total = len(orders)
        new_count = len([o for o in orders if o["status"] == "new"])
        preparing_count = len([o for o in orders if o["status"] == "preparing"])

        # Выручка за сегодня
        today = datetime.now().strftime("%Y-%m-%d")
        today_orders = [o for o in orders if o["created_at"].startswith(today)]
        revenue = sum(o["total_price"] for o in today_orders)

        self.total_orders_label.config(text=str(total))
        self.new_orders_label.config(text=str(new_count))
        self.preparing_label.config(text=str(preparing_count))
        self.revenue_label.config(text=f"{revenue:,} сум")

    def auto_refresh_loop(self):
        while self.auto_refresh:
            time.sleep(10)  # Обновление каждые 10 секунд
            try:
                # Запускаем загрузку в отдельном потоке
                threading.Thread(target=self._load_orders_thread, daemon=True).start()
            except:
                break


if __name__ == "__main__":
    root = tk.Tk()
    app = PizzaAdminApp(root)
    root.mainloop()