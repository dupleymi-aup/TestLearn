"""
Маршруты аутентификации пользователей
"""

import secrets
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from datetime import datetime

from app.deps.auth import (
    hash_password, verify_password, validate_username,
    validate_email, validate_password as validate_pwd,
    generate_csrf_token
)
from app.services.data_service import (
    create_user, get_user_by_username, get_user_by_id
)

router = APIRouter()


def get_current_user_from_session(request: Request):
    """Получить текущего пользователя из сессии."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(int(user_id))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа."""
    templates = request.app.state.templates

    # Если уже авторизован - перенаправляем на главную
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)

    csrf_token = generate_csrf_token()
    # Сохраняем токен в сессии для валидации при отправке формы
    request.session["csrf_token"] = csrf_token

    return templates.TemplateResponse(request, "login.html", {
        "csrf_token": csrf_token,
        "error": None
    })


def _get_csrf_error(request: Request, form_csrf_token: str) -> str | None:
    """Validate CSRF token and return error message if invalid, else None."""
    stored_token = request.session.get("csrf_token")
    if not form_csrf_token or not stored_token or not secrets.compare_digest(form_csrf_token, stored_token):
        return "Ошибка безопасности: неверный CSRF токен. Пожалуйста, обновите страницу и попробуйте снова."
    return None


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request):
    """Обработка входа."""
    templates = request.app.state.templates
    form = await request.form()

    # Валидация CSRF токена
    csrf_error = _get_csrf_error(request, form.get("csrf_token"))
    if csrf_error:
        return templates.TemplateResponse(request, "login.html", {
            "csrf_token": generate_csrf_token(),
            "error": csrf_error
        })

    username = form.get("username", "").strip()
    password = form.get("password", "")

    if not username or not password:
        return templates.TemplateResponse(request, "login.html", {
            "csrf_token": generate_csrf_token(),
            "error": "Введите имя пользователя и пароль"
        })

    user = get_user_by_username(username)

    if not user:
        return templates.TemplateResponse(request, "login.html", {
            "csrf_token": generate_csrf_token(),
            "error": "Неверное имя пользователя или пароль"
        })

    if not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "login.html", {
            "csrf_token": generate_csrf_token(),
            "error": "Неверное имя пользователя или пароль"
        })

    # Создаём сессию
    request.session["user_id"] = str(user.id)
    request.session["username"] = user.username

    return RedirectResponse(url="/", status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации."""
    templates = request.app.state.templates

    # Если уже авторизован - перенаправляем на главную
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)

    csrf_token = generate_csrf_token()
    # Сохраняем токен в сессии для валидации при отправке формы
    request.session["csrf_token"] = csrf_token

    return templates.TemplateResponse(request, "register.html", {
        "csrf_token": csrf_token,
        "errors": {},
        "form_data": {}
    })


@router.post("/register", response_class=HTMLResponse)
async def register_submit(request: Request):
    """Обработка регистрации."""
    templates = request.app.state.templates
    form = await request.form()

    # Валидация CSRF токена
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        return templates.TemplateResponse(request, "register.html", {
            "csrf_token": generate_csrf_token(),
            "errors": {"general": "Ошибка безопасности: неверный CSRF токен. Пожалуйста, обновите страницу и попробуйте снова."},
            "form_data": {}
        })

    username = form.get("username", "").strip()
    email = form.get("email", "").strip()
    password = form.get("password", "")
    confirm_password = form.get("confirm_password", "")

    errors = {}

    # Валидация
    if not validate_username(username):
        errors["username"] = "Имя должно содержать 3-32 символа (буквы, цифры, _)"

    if not validate_email(email):
        errors["email"] = "Некорректный email"

    pwd_valid, pwd_error = validate_pwd(password)
    if not pwd_valid:
        errors["password"] = pwd_error

    if password != confirm_password:
        errors["confirm_password"] = "Пароли не совпадают"

    if errors:
        return templates.TemplateResponse(request, "register.html", {
            "csrf_token": generate_csrf_token(),
            "errors": errors,
            "form_data": {"username": username, "email": email}
        })

    # Создание пользователя
    success, message = create_user(username, email, password)

    if not success:
        return templates.TemplateResponse(request, "register.html", {
            "csrf_token": generate_csrf_token(),
            "errors": {"general": message},
            "form_data": {"username": username, "email": email}
        })

    # Автоматический вход после регистрации
    user = get_user_by_username(username)
    request.session["user_id"] = str(user.id)
    request.session["username"] = user.username

    return RedirectResponse(url="/", status_code=303)


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Выход из системы."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Страница профиля."""
    templates = request.app.state.templates
    
    user = get_current_user_from_session(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    from app.services.data_service import get_user_stats, get_user_achievements
    
    user_stats = get_user_stats(user.id)
    achievements = get_user_achievements(user.id)
    
    return templates.TemplateResponse(request, "profile.html", {
        "user": user,
        "user_stats": user_stats,
        "achievements": achievements,
        "csrf_token": generate_csrf_token()
    })
