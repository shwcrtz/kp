import unittest
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import Restaurant, MenuItem, Order, CartItem, Customer, Courier, OrderStatus, CourierStatus

class TestModels(unittest.TestCase):
    """Тесты для моделей данных"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.test_restaurant = Restaurant(
            id="test_1",
            name="Test Restaurant",
            cuisine="Italian",
            delivery_time="30 min",
            rating=4.5,
            address="Test Address"
        )
        
        self.test_menu_item = MenuItem(
            id="item_1",
            restaurant_id="rest_1",
            name="Test Pizza",
            description="Test description",
            price=10.99,
            category="Pizza"
        )
        
        self.test_customer = Customer(
            id="cust_1",
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890",
            address="Test Address"
        )
        
        self.test_courier = Courier(
            id="cour_1",
            name="Test Courier",
            phone="+0987654321",
            vehicle_type="bicycle",
            status=CourierStatus.AVAILABLE
        )

    def test_restaurant_model(self):
        """Тест создания модели ресторана"""
        self.assertEqual(self.test_restaurant.id, "test_1")
        self.assertEqual(self.test_restaurant.name, "Test Restaurant")
        self.assertEqual(self.test_restaurant.cuisine, "Italian")
        self.assertEqual(self.test_restaurant.is_active, True)

    def test_menu_item_model(self):
        """Тест создания модели товара меню"""
        self.assertEqual(self.test_menu_item.price, 10.99)
        self.assertEqual(self.test_menu_item.category, "Pizza")
        self.assertEqual(self.test_menu_item.is_available, True)

    def test_customer_model(self):
        """Тест создания модели клиента"""
        self.assertEqual(self.test_customer.name, "Test Customer")
        self.assertEqual(self.test_customer.email, "test@example.com")
        self.assertEqual(self.test_customer.phone, "+1234567890")

    def test_courier_model(self):
        """Тест создания модели курьера"""
        self.assertEqual(self.test_courier.name, "Test Courier")
        self.assertEqual(self.test_courier.vehicle_type, "bicycle")
        self.assertEqual(self.test_courier.status, CourierStatus.AVAILABLE)

    def test_order_model(self):
        """Тест создания модели заказа"""
        order = Order(
            id="order_1",
            customer_id="user_1",
            restaurant_id="rest_1",
            items=[{"item": "pizza", "quantity": 2}],
            total_amount=25.98,
            status=OrderStatus.PENDING,
            delivery_address="Test Address",
            created_at=datetime.now()
        )
        
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.total_amount, 25.98)

    def test_cart_item_model(self):
        """Тест создания модели элемента корзины"""
        cart_item = CartItem(menu_item_id="item_1", quantity=2)
        self.assertEqual(cart_item.menu_item_id, "item_1")
        self.assertEqual(cart_item.quantity, 2)

class TestEnums(unittest.TestCase):
    """Тесты для Enum классов"""
    
    def test_order_status_enum(self):
        """Тест значений OrderStatus enum"""
        self.assertEqual(OrderStatus.PENDING.value, "pending")
        self.assertEqual(OrderStatus.CONFIRMED.value, "confirmed")
        self.assertEqual(OrderStatus.DELIVERED.value, "delivered")
        
    def test_courier_status_enum(self):
        """Тест значений CourierStatus enum"""
        self.assertEqual(CourierStatus.AVAILABLE.value, "available")
        self.assertEqual(CourierStatus.BUSY.value, "busy")
        self.assertEqual(CourierStatus.OFFLINE.value, "offline")

# Executing the tests
if __name__ == "__main__":
    unittest.main()
    