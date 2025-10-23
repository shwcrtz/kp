from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from enum import Enum
import sqlite3
import json
from contextlib import contextmanager

app = FastAPI(title="Food Delivery API", version="1.0.0")

# Настройка базы данных SQLite
DATABASE_NAME = "Курсач.db"

# Контекстный менеджер для подключения к БД
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        print(f"❌ Ошибка подключения к SQLite: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        if conn:
            conn.close()

def init_database():
    """Инициализация базы данных и создание таблиц"""
    print("🔄 Инициализация SQLite базы данных...")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица клиентов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Таблица 'customers' создана/проверена")
            
            # Таблица ресторанов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS restaurants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    cuisine TEXT NOT NULL,
                    delivery_time TEXT NOT NULL,
                    rating REAL DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT 1,
                    address TEXT NOT NULL
                )
            ''')
            print("✅ Таблица 'restaurants' создана/проверена")
            
            # Таблица позиций меню
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS menu_items (
                    id TEXT PRIMARY KEY,
                    restaurant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    is_available BOOLEAN DEFAULT 1,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
                )
            ''')
            print("✅ Таблица 'menu_items' создана/проверена")
            
            # Таблица курьеров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS couriers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    status TEXT DEFAULT 'available',
                    current_location TEXT
                )
            ''')
            print("✅ Таблица 'couriers' создана/проверена")
            
            # Таблица заказов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    restaurant_id TEXT NOT NULL,
                    courier_id TEXT,
                    items TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    delivery_address TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    estimated_delivery_time TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id),
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants (id),
                    FOREIGN KEY (courier_id) REFERENCES couriers (id)
                )
            ''')
            print("✅ Таблица 'orders' создана/проверена")
            
            # Таблица корзин
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carts (
                    customer_id TEXT PRIMARY KEY,
                    items TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            ''')
            print("✅ Таблица 'carts' создана/проверена")
            
            conn.commit()
            print("🎉 Все таблицы SQLite успешно созданы!")
            
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")

# Enum для статусов
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COOKING = "cooking"
    READY_FOR_DELIVERY = "ready_for_delivery"
    ON_WAY = "on_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class CourierStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

# Модели данных
class Customer(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    address: str
    created_at: Optional[datetime] = None

class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: str
    delivery_time: str
    rating: float = 0.0
    is_active: bool = True
    address: str

class MenuItem(BaseModel):
    id: str
    restaurant_id: str
    name: str
    description: str
    price: float
    category: str
    is_available: bool = True

class Courier(BaseModel):
    id: str
    name: str
    phone: str
    vehicle_type: str
    status: CourierStatus = CourierStatus.AVAILABLE
    current_location: Optional[str] = None

class CartItem(BaseModel):
    menu_item_id: str
    quantity: int

class Order(BaseModel):
    id: str
    customer_id: str
    restaurant_id: str
    courier_id: Optional[str] = None
    items: List[dict]
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    delivery_address: str
    created_at: Optional[datetime] = None
    estimated_delivery_time: Optional[str] = None

# Вспомогательные функции для работы с БД
def dict_to_json(data: dict) -> str:
    """Конвертирует словарь в JSON строку для хранения в БД"""
    return json.dumps(data, ensure_ascii=False)

def json_to_dict(json_str: str) -> dict:
    """Конвертирует JSON строку из БД в словарь"""
    return json.loads(json_str) if json_str else {}

def check_tables_exist():
    """Проверяет существование таблиц"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table['name'] for table in tables]
            print(f"📊 Существующие таблицы: {table_names}")
            return table_names
    except Exception as e:
        print(f"❌ Ошибка при проверке таблиц: {e}")
        return []

# Endpoint'ы API

@app.get("/")
async def root():
    return {"message": "Food Delivery API", "status": "active", "database": "SQLite"}

@app.get("/debug/tables")
async def debug_tables():
    """Endpoint для отладки - показывает все таблицы"""
    tables = check_tables_exist()
    return {"tables": tables}

# Customers (клиенты)
@app.post("/customers", response_model=Customer)
async def create_customer(customer: Customer):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO customers (id, name, email, phone, address, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer.id, customer.name, customer.email, customer.phone, 
                  customer.address, customer.created_at or datetime.now()))
            conn.commit()
            return customer
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Customer already exists")

@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return Customer(**dict(row))

# Restaurants (рестораны)
@app.get("/restaurants", response_model=List[Restaurant])
async def get_restaurants(cuisine: Optional[str] = None, is_active: bool = True):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM restaurants WHERE is_active = ?'
        params = [1 if is_active else 0]
        
        if cuisine:
            query += ' AND cuisine = ?'
            params.append(cuisine)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [Restaurant(**dict(row)) for row in rows]

@app.get("/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return Restaurant(**dict(row))

# Menu Items (позиции в меню)
@app.get("/restaurants/{restaurant_id}/menu")
async def get_restaurant_menu(restaurant_id: str, category: Optional[str] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Проверяем существование ресторана
        cursor.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,))
        restaurant_row = cursor.fetchone()
        if not restaurant_row:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        restaurant = Restaurant(**dict(restaurant_row))
        
        # Получаем меню
        query = 'SELECT * FROM menu_items WHERE restaurant_id = ? AND is_available = 1'
        params = [restaurant_id]
        
        if category:
            query += ' AND category = ?'
            params.append(category)
            
        cursor.execute(query, params)
        menu_rows = cursor.fetchall()
        menu_items = [MenuItem(**dict(row)) for row in menu_rows]
        
        return {
            "restaurant": restaurant,
            "menu_items": menu_items
        }

@app.get("/menu/items/{item_id}")
async def get_menu_item(item_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM menu_items WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return MenuItem(**dict(row))

# Couriers (курьеры)
@app.post("/couriers", response_model=Courier)
async def create_courier(courier: Courier):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO couriers (id, name, phone, vehicle_type, status, current_location)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (courier.id, courier.name, courier.phone, courier.vehicle_type, 
                  courier.status.value, courier.current_location))
            conn.commit()
            return courier
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Courier already exists")

@app.get("/couriers", response_model=List[Courier])
async def get_couriers(status: Optional[CourierStatus] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM couriers'
        params = []
        
        if status:
            query += ' WHERE status = ?'
            params.append(status.value)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [Courier(**dict(row)) for row in rows]

@app.get("/couriers/{courier_id}")
async def get_courier(courier_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM couriers WHERE id = ?', (courier_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Courier not found")
        return Courier(**dict(row))

@app.put("/couriers/{courier_id}/status")
async def update_courier_status(courier_id: str, status: CourierStatus):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM couriers WHERE id = ?', (courier_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Courier not found")
        
        cursor.execute('UPDATE couriers SET status = ? WHERE id = ?', (status.value, courier_id))
        conn.commit()
        
        cursor.execute('SELECT * FROM couriers WHERE id = ?', (courier_id,))
        updated_courier = Courier(**dict(cursor.fetchone()))
        return {"message": f"Courier status updated to {status}", "courier": updated_courier}

# Корзина
@app.post("/customers/{customer_id}/cart")
async def add_to_cart(customer_id: str, cart_item: CartItem):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Проверяем существование клиента
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Проверяем существование товара
        cursor.execute('SELECT * FROM menu_items WHERE id = ? AND is_available = 1', (cart_item.menu_item_id,))
        menu_row = cursor.fetchone()
        if not menu_row:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        # Получаем текущую корзину
        cursor.execute('SELECT items FROM carts WHERE customer_id = ?', (customer_id,))
        cart_row = cursor.fetchone()
        
        if cart_row and cart_row['items']:
            current_items = json_to_dict(cart_row['items'])
        else:
            current_items = []
        
        # Добавляем новый товар
        current_items.append(cart_item.dict())
        
        # Сохраняем корзину
        if cart_row:
            cursor.execute('UPDATE carts SET items = ? WHERE customer_id = ?', 
                         (dict_to_json(current_items), customer_id))
        else:
            cursor.execute('INSERT INTO carts (customer_id, items) VALUES (?, ?)', 
                         (customer_id, dict_to_json(current_items)))
        
        conn.commit()
        return {"message": "Item added to cart", "cart": current_items}

@app.get("/customers/{customer_id}/cart")
async def get_cart(customer_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Проверяем существование клиента
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")
        
        cursor.execute('SELECT items FROM carts WHERE customer_id = ?', (customer_id,))
        cart_row = cursor.fetchone()
        
        if not cart_row or not cart_row['items']:
            return {"items": [], "total_amount": 0}
        
        cart_items = json_to_dict(cart_row['items'])
        total = 0
        
        for item in cart_items:
            cursor.execute('SELECT price FROM menu_items WHERE id = ?', (item['menu_item_id'],))
            menu_row = cursor.fetchone()
            if menu_row:
                total += menu_row['price'] * item['quantity']
        
        return {
            "items": cart_items,
            "total_amount": total
        }

@app.delete("/customers/{customer_id}/cart")
async def clear_cart(customer_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")
        
        cursor.execute('DELETE FROM carts WHERE customer_id = ?', (customer_id,))
        conn.commit()
        
        return {"message": "Cart cleared successfully"}

# Orders (заказы)
@app.post("/orders")
async def create_order(customer_id: str, delivery_address: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Получаем корзину
        cursor.execute('SELECT items FROM carts WHERE customer_id = ?', (customer_id,))
        cart_row = cursor.fetchone()
        
        if not cart_row or not cart_row['items']:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        cart_items = json_to_dict(cart_row['items'])
        
        # Проверяем, что все товары из одного ресторана
        restaurant_id = None
        total_amount = 0
        order_items = []
        
        for item in cart_items:
            cursor.execute('SELECT * FROM menu_items WHERE id = ?', (item['menu_item_id'],))
            menu_row = cursor.fetchone()
            if not menu_row:
                continue
                
            menu_item = MenuItem(**dict(menu_row))
            if not restaurant_id:
                restaurant_id = menu_item.restaurant_id
            elif menu_item.restaurant_id != restaurant_id:
                raise HTTPException(status_code=400, detail="All items must be from the same restaurant")
            
            item_total = menu_item.price * item['quantity']
            total_amount += item_total
            
            order_items.append({
                "menu_item": menu_item.dict(),
                "quantity": item['quantity'],
                "item_total": item_total
            })
        
        if not restaurant_id:
            raise HTTPException(status_code=400, detail="No valid items in cart")
        
        # Находим доступного курьера
        cursor.execute('SELECT * FROM couriers WHERE status = ? LIMIT 1', (CourierStatus.AVAILABLE.value,))
        available_courier_row = cursor.fetchone()
        available_courier = Courier(**dict(available_courier_row)) if available_courier_row else None
        
        # Создаем заказ
        order_id = str(uuid.uuid4())
        order_data = Order(
            id=order_id,
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            courier_id=available_courier.id if available_courier else None,
            items=order_items,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            delivery_address=delivery_address,
            created_at=datetime.now(),
            estimated_delivery_time="30-40 min"
        )
        
        # Сохраняем заказ в БД
        cursor.execute('''
            INSERT INTO orders (id, customer_id, restaurant_id, courier_id, items, 
                              total_amount, status, delivery_address, created_at, estimated_delivery_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, customer_id, restaurant_id, available_courier.id if available_courier else None,
              dict_to_json(order_items), total_amount, OrderStatus.PENDING.value, 
              delivery_address, datetime.now(), "30-40 min"))
        
        # Обновляем статус курьера если он назначен
        if available_courier:
            cursor.execute('UPDATE couriers SET status = ? WHERE id = ?', 
                         (CourierStatus.BUSY.value, available_courier.id))
        
        # Очищаем корзину
        cursor.execute('DELETE FROM carts WHERE customer_id = ?', (customer_id,))
        
        conn.commit()
        
        return {
            "message": "Order created successfully",
            "order_id": order_id,
            "order": order_data
        }

@app.get("/orders", response_model=List[Order])
async def get_orders(customer_id: Optional[str] = None, status: Optional[OrderStatus] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM orders'
        params = []
        
        if customer_id:
            query += ' WHERE customer_id = ?'
            params.append(customer_id)
            if status:
                query += ' AND status = ?'
                params.append(status.value)
        elif status:
            query += ' WHERE status = ?'
            params.append(status.value)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        orders = []
        for row in rows:
            order_dict = dict(row)
            order_dict['items'] = json_to_dict(order_dict['items'])
            orders.append(Order(**order_dict))
        
        return orders

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_dict = dict(row)
        order_dict['items'] = json_to_dict(order_dict['items'])
        return Order(**order_dict)

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, new_status: OrderStatus):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Получаем текущий заказ
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Обновляем статус
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status.value, order_id))
        
        # Если заказ доставлен, освобождаем курьера
        if new_status == OrderStatus.DELIVERED and row['courier_id']:
            cursor.execute('UPDATE couriers SET status = ? WHERE id = ?', 
                         (CourierStatus.AVAILABLE.value, row['courier_id']))
        
        conn.commit()
        
        # Возвращаем обновленный заказ
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        updated_row = cursor.fetchone()
        order_dict = dict(updated_row)
        order_dict['items'] = json_to_dict(order_dict['items'])
        
        return {"message": f"Order status updated to {new_status}", "order": Order(**order_dict)}

@app.put("/orders/{order_id}/assign-courier")
async def assign_courier_to_order(order_id: str, courier_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Проверяем существование заказа
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order_row = cursor.fetchone()
        if not order_row:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Проверяем существование курьера
        cursor.execute('SELECT * FROM couriers WHERE id = ?', (courier_id,))
        courier_row = cursor.fetchone()
        if not courier_row:
            raise HTTPException(status_code=404, detail="Courier not found")
        
        courier = Courier(**dict(courier_row))
        if courier.status != CourierStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail="Courier is not available")
        
        # Если у заказа уже был курьер, освобождаем его
        if order_row['courier_id']:
            cursor.execute('UPDATE couriers SET status = ? WHERE id = ?', 
                         (CourierStatus.AVAILABLE.value, order_row['courier_id']))
        
        # Назначаем нового курьера
        cursor.execute('UPDATE orders SET courier_id = ? WHERE id = ?', (courier_id, order_id))
        cursor.execute('UPDATE couriers SET status = ? WHERE id = ?', 
                     (CourierStatus.BUSY.value, courier_id))
        
        conn.commit()
        
        # Возвращаем обновленный заказ
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        updated_order_row = cursor.fetchone()
        order_dict = dict(updated_order_row)
        order_dict['items'] = json_to_dict(order_dict['items'])
        
        return {"message": f"Courier {courier_id} assigned to order {order_id}", "order": Order(**order_dict)}

# Инициализация базы данных при старте
@app.on_event("startup")
async def startup_event():
    print("🚀 Запуск приложения с SQLite...")
    init_database()
    await insert_test_data()

async def insert_test_data():
    """Вставка тестовых данных в базу"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже данные
            cursor.execute('SELECT COUNT(*) as count FROM customers')
            result = cursor.fetchone()
            count = result['count'] if isinstance(result, dict) else result[0]
            
            if count == 0:
                print("📝 Добавление тестовых данных...")
                
                # Добавляем тестовых клиентов
                test_customers = [
                    ("c1", "John Doe", "john@example.com", "+1234567890", "123 Main St, City"),
                    ("c2", "Jane Smith", "jane@example.com", "+0987654321", "456 Oak Ave, Town")
                ]
                
                for customer in test_customers:
                    cursor.execute('''
                        INSERT OR IGNORE INTO customers (id, name, email, phone, address)
                        VALUES (?, ?, ?, ?, ?)
                    ''', customer)
                
                # Добавляем тестовые рестораны
                test_restaurants = [
                    ("r1", "Pizza Palace", "Italian", "30-40 min", 4.5, "789 Pizza St, City"),
                    ("r2", "Sushi Spot", "Japanese", "40-50 min", 4.7, "321 Sushi Rd, Town")
                ]
                
                for restaurant in test_restaurants:
                    cursor.execute('''
                        INSERT OR IGNORE INTO restaurants (id, name, cuisine, delivery_time, rating, address)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', restaurant)
                
                # Добавляем тестовые товары в меню
                test_menu_items = [
                    ("m1", "r1", "Margherita Pizza", "Classic pizza with tomato and mozzarella", 12.99, "Pizza"),
                    ("m2", "r1", "Pepperoni Pizza", "Pizza with pepperoni and cheese", 14.99, "Pizza"),
                    ("m3", "r2", "California Roll", "Crab, avocado, cucumber", 8.99, "Sushi"),
                    ("m4", "r2", "Salmon Nigiri", "Fresh salmon on rice", 6.99, "Sushi")
                ]
                
                for menu_item in test_menu_items:
                    cursor.execute('''
                        INSERT OR IGNORE INTO menu_items (id, restaurant_id, name, description, price, category)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', menu_item)
                
                # Добавляем тестовых курьеров
                test_couriers = [
                    ("courier1", "Mike Courier", "+1112223333", "bicycle", "available", "City Center"),
                    ("courier2", "Sarah Driver", "+4445556666", "car", "available", "North District")
                ]
                
                for courier in test_couriers:
                    cursor.execute('''
                        INSERT OR IGNORE INTO couriers (id, name, phone, vehicle_type, status, current_location)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', courier)
                
                conn.commit()
                print("✅ Тестовые данные добавлены!")
            else:
                print("✅ Данные уже существуют в базе")
                
    except Exception as e:
        print(f"❌ Ошибка при добавлении тестовых данных: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)