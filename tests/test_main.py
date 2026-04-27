import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the parent directory to sys.path so we can import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from main import app
from app.database.db import init_database
from app.services.data_service import create_category

# Initialize the database before running tests
init_database()

# Seed data for tests
def seed_test_data():
    """Создать тестовые данные."""
    create_category("Тестовая категория", "test-category", "Описание для тестов")
    create_category("Функциональное тестирование", "functional", "Проверка функциональности")

seed_test_data()

# Setup templates in app state for testing
from fastapi.templating import Jinja2Templates
import os
templates_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
app.state.templates = Jinja2Templates(directory=templates_path)

client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    # Check that page loads successfully
    assert response.status_code == 200


def test_glossary_page():
    response = client.get("/glossary")
    assert response.status_code == 200


def test_about_page():
    response = client.get("/about")
    assert response.status_code == 200