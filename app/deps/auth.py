"""
Зависимости и утилиты для маршрутов
"""

import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import re

from app.database.db import get_db


# ====== АУТЕНТИФИКАЦИЯ АДМИНИСТРАТОРА ======

def get_admin_password_hash() -> str:
    """Получить хеш пароля администратора из переменных окружения."""
    password = os.getenv("ADMIN_PASSWORD", "admin")
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    """Хеширование пароля с солью."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Проверка пароля против хеша."""
    try:
        salt, expected_hash = stored_hash.split(":")
        actual_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return secrets.compare_digest(actual_hash, expected_hash)
    except (ValueError, AttributeError):
        return False


def create_admin_session(username: str) -> str:
    """Создать новую сессию для администратора."""
    session_id = str(uuid.uuid4())
    expires = datetime.now() + timedelta(hours=24)
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO admin_sessions (id, username, expires, created_at) VALUES (?, ?, ?, ?)",
            (session_id, username, expires.isoformat(), datetime.now().isoformat())
        )
        conn.commit()
    return session_id


def verify_admin_session(request: Request) -> bool:
    """Проверить, существует ли действительная сессия администратора."""
    session_id = request.cookies.get("admin_session")
    if not session_id:
        return False
    
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT username, expires FROM admin_sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False
        expires = datetime.fromisoformat(row["expires"])
        if expires < datetime.now():
            # Сессия истекла, удаляем её
            conn.execute("DELETE FROM admin_sessions WHERE id = ?", (session_id,))
            conn.commit()
            return False
        return True


async def get_current_admin(request: Request):
    """Dependency для защиты маршрутов админ-панели."""
    if not verify_admin_session(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True


# ====== ВАЛИДАЦИЯ ВХОДНЫХ ДАННЫХ ======

def validate_username(username: str) -> bool:
    """Валидация имени пользователя: 3-32 символа, буквы, цифры, подчёркивания."""
    pattern = r'^[a-zA-Z0-9_]{3,32}$'
    return bool(re.match(pattern, username))


def validate_email(email: str) -> bool:
    """Валидация email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Валидация пароля.
    Возвращает (успех, сообщение об ошибке).
    """
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    if not any(c.isupper() for c in password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    if not any(c.isdigit() for c in password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    return True, ""


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Санитизация входных данных: удаление опасных символов."""
    if not text:
        return ""
    # Ограничение длины
    text = text[:max_length]
    # Удаление потенциально опасных HTML-тегов
    text = re.sub(r'<[^>]*>', '', text)
    return text.strip()


# ===== CSRF ЗАЩИТА ======

def generate_csrf_token() -> str:
    """Генерация CSRF токена."""
    return secrets.token_urlsafe(32)


def validate_csrf_token(request: Request, token: str) -> bool:
    """Валидация CSRF токена."""
    stored_token = request.session.get("csrf_token")
    if not stored_token:
        return False
    return secrets.compare_digest(stored_token, token)


async def csrf_protect(request: Request, form_data: dict = None):
    """Dependency для CSRF защиты POST запросов."""
    if request.method in ["POST", "PUT", "DELETE"]:
        token = None
        if form_data and "csrf_token" in form_data:
            token = form_data.get("csrf_token")
        else:
            token = request.headers.get("X-CSRF-Token")
        
        if not token or not validate_csrf_token(request, token):
            raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    return True
