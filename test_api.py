import unittest
import os
import sqlite3
import time
from fastapi.testclient import TestClient

from main import app, init_database

class TestCustomerAPI(unittest.TestCase):
    """Тесты API клиентов"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.client = TestClient(app)
        self.cleanup_database()
        self.setup_test_database()
    
    def cleanup_database(self):
        """Очистка базы данных"""
        # Даем время на закрытие соединений
        time.sleep(0.1)
        if os.path.exists("Курсач.db"):
            try:
                os.remove("Курсач.db")
            except PermissionError:
                # Если файл занят, пропускаем удаление
                pass
    
    def setup_test_database(self):
        """Создание тестовой базы данных"""
        # Инициализируем чистую базу данных
        init_database()
        
        # Добавляем тестовые данные
        conn = sqlite3.connect("Курсач.db")
        cursor = conn.cursor()
        
        # Добавляем тестовые рестораны
        cursor.execute('''
            INSERT OR REPLACE INTO restaurants (id, name, cuisine, delivery_time, rating, address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("r1", "Pizza Palace", "Italian", "30-40 min", 4.5, "123 Pizza St"))
        
        cursor.execute('''
            INSERT OR REPLACE INTO restaurants (id, name, cuisine, delivery_time, rating, address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("r2", "Sushi Spot", "Japanese", "40-50 min", 4.7, "456 Sushi Rd"))
        
        conn.commit()
        conn.close()

    def tearDown(self):
        """Очистка после каждого теста"""
        # Не удаляем базу данных, просто очищаем таблицы
        try:
            conn = sqlite3.connect("Курсач.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers")
            cursor.execute("DELETE FROM restaurants")
            cursor.execute("DELETE FROM menu_items")
            conn.commit()
            conn.close()
        except:
            pass

    def test_create_customer_success(self):
        """Тест успешного создания клиента"""
        customer_data = {
            "id": "test_customer_1",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "address": "123 Main St"
        }
        
        response = self.client.post("/customers", json=customer_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "John Doe")
        self.assertEqual(data["email"], "john@example.com")

    def test_get_customer_success(self):
        """Тест успешного получения клиента"""
        # Сначала создаем клиента
        customer_data = {
            "id": "get_test_customer",
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+0987654321",
            "address": "456 Oak Ave"
        }
        create_response = self.client.post("/customers", json=customer_data)
        self.assertEqual(create_response.status_code, 200)
        
        # Затем получаем его
        response = self.client.get("/customers/get_test_customer")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Jane Smith")
        self.assertEqual(data["email"], "jane@example.com")


class TestRestaurantAPI(unittest.TestCase):
    """Тесты API ресторанов"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.client = TestClient(app)
        self.cleanup_database()
        self.setup_test_database()
    
    def cleanup_database(self):
        """Очистка базы данных"""
        time.sleep(0.1)
        if os.path.exists("Курсач.db"):
            try:
                os.remove("Курсач.db")
            except PermissionError:
                pass
    
    def setup_test_database(self):
        """Создание тестовой базы данных"""
        init_database()
        
        conn = sqlite3.connect("Курсач.db")
        cursor = conn.cursor()
        
        # Добавляем тестовые рестораны
        test_restaurants = [
            ("r1", "Pizza Palace", "Italian", "30-40 min", 4.5, 1, "123 Pizza St"),
            ("r2", "Sushi Spot", "Japanese", "40-50 min", 4.7, 1, "456 Sushi Rd"),
            ("r3", "Burger Joint", "American", "25-35 min", 4.2, 1, "789 Burger Ave"),
            ("r4", "Inactive Restaurant", "French", "50-60 min", 4.0, 0, "000 Inactive St")
        ]
        
        for restaurant in test_restaurants:
            cursor.execute('''
                INSERT OR REPLACE INTO restaurants (id, name, cuisine, delivery_time, rating, is_active, address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', restaurant)
        
        conn.commit()
        conn.close()

    def tearDown(self):
        """Очистка после каждого теста"""
        try:
            conn = sqlite3.connect("Курсач.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM restaurants")
            conn.commit()
            conn.close()
        except:
            pass

    def test_get_all_restaurants(self):
        """Тест получения всех активных ресторанов"""
        response = self.client.get("/restaurants")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)

    def test_get_restaurants_filter_by_cuisine(self):
        """Тест фильтрации ресторанов по кухне"""
        response = self.client.get("/restaurants?cuisine=Italian")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Pizza Palace")

    def test_get_restaurants_inactive(self):
        """Тест получения неактивных ресторанов"""
        response = self.client.get("/restaurants?is_active=false")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Inactive Restaurant")

    def test_get_restaurant_by_id_success(self):
        """Тест успешного получения ресторана по ID"""
        response = self.client.get("/restaurants/r1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "r1")
        self.assertEqual(data["name"], "Pizza Palace")

class TestRootEndpoint(unittest.TestCase):
    """Тесты корневого endpoint"""
    
    def setUp(self):
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Тест корневого endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Food Delivery API")


if __name__ == "__main__":
    unittest.main()
