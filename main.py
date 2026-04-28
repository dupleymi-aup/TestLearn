"""
FastAPI приложение: Учебная платформа по основам тестирования программного обеспечения
Модульная версия с разделением на database, routes, deps, models
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Import database initialization
from app.database.db import init_database, DB_NAME

# Import routes
from app.routes.main_routes import router as main_router
from app.routes.auth_routes import router as auth_router
from app.routes.admin_routes import router as admin_router


# ====== LIFESPAN CONTEXT MANAGER ======

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Современный lifespan API для инициализации приложения."""
    # Startup: инициализация БД
    init_database()

    # Настройка шаблонов и статики
    static_path = os.path.join(os.path.dirname(__file__), "static")
    templates_path = os.path.join(os.path.dirname(__file__), "templates")

    # Монтируем статику
    if os.path.exists(static_path):
        app.mount("/static", StaticFiles(directory=static_path), name="static")

    # Сохраняем templates в state для доступа из роутов
    app.state.templates = Jinja2Templates(directory=templates_path)
    app.state.static_path = static_path

    yield

    # Shutdown: очистка ресурсов (если нужно)
    pass


# ====== ПРИЛОЖЕНИЕ ======

app = FastAPI(
    title="TestLearn - Платформа для изучения тестирования ПО",
    description="Учебная платформа по основам тестирования программного обеспечения",
    version="2.0.0",
    lifespan=lifespan
)

# Добавляем middleware для сессий (нужен SECRET_KEY)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


# ====== МАРШРУТЫ ======

# Подключаем роуты
app.include_router(main_router)
app.include_router(auth_router)
app.include_router(admin_router)


# ====== ОБРАБОТЧИКИ ОШИБОК ======

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Обработчик ошибки 404."""
    templates = getattr(app.state, 'templates', None)
    if templates:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )
    return HTMLResponse(content="Страница не найдена", status_code=404)


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Обработчик ошибки 500."""
    templates = getattr(app.state, 'templates', None)
    if templates:
        return templates.TemplateResponse(
            "500.html",
            {"request": request},
            status_code=500
        )
    return HTMLResponse(content="Внутренняя ошибка сервера", status_code=500)


# ====== ЗАПУСК ======

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
