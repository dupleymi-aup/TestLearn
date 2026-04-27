import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the parent directory to sys.path so we can import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from main import app, init_db, seed_data

# Initialize the database before running tests
init_db()
seed_data()

client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "TestLearn" in response.text


def test_api_categories():
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # We expect at least one category from the seed data
    assert len(data) > 0
    # Check structure of first category
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "description" in first