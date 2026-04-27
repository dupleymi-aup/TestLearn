"""Конфигурация приложения TestLearn."""

import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent

# База данных
DB_NAME = os.getenv("TESTLEARN_DB", "testlearn.db")

# Администратор
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Приложение
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
SECRET_KEY = os.getenv("SECRET_KEY", "testlearn-secret-key-change-in-production")

# Сессия
SESSION_COOKIE_NAME = "testlearn_session"
SESSION_MAX_AGE = 30 * 24 * 60 * 60  # 30 дней
ADMIN_SESSION_COOKIE = "admin_session"
ADMIN_SESSION_HOURS = 24
