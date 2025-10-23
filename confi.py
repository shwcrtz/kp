# conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="session")
def client():
    """Фикстура для тестового клиента"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def cleanup():
    """Автоматическая очистка после каждого теста"""
    from main import restaurants_db, menu_items_db, user_carts, orders_db
    yield
    restaurants_db.clear()
    menu_items_db.clear()
    user_carts.clear()
    orders_db.clear()