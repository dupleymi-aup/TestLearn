# TestLearn — Быстрый старт

## 🚀 Локальный запуск (рекомендуется)

### Вариант 1: Простой запуск

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить приложение
python main.py
```

Откройте браузер: http://localhost:8000

### Вариант 2: Использование Makefile

```bash
# Показать все доступные команды
make help

# Установить и запустить
make dev

# Только запуск
make run

# Запустить тесты
make test

# Очистить кэш
make clean
```

### Вариант 3: Docker (для изоляции)

```bash
# Development режим
docker-compose -f docker-compose.dev.yml up --build

# Production режим
docker-compose -f docker-compose.prod.yml up --build
```

## 📁 Структура проекта

```
TestLearn/
├── app/                    # Основной код приложения
│   ├── database/          # Конфигурация БД
│   ├── models/            # Pydantic схемы
│   ├── deps/              # Зависимости (auth, CSRF)
│   ├── services/          # Бизнес-логика
│   └── routes/            # Маршруты (main, auth, admin)
├── templates/             # HTML шаблоны
├── static/                # Статические файлы
│   ├── css/style.css     # Стили
│   └── js/main.js        # JavaScript
├── tests/                 # Тесты
├── .env                   # Переменные окружения (локально)
├── .env.example           # Пример конфигурации
├── main.py                # Точка входа
└── requirements.txt       # Зависимости
```

## 🔐 Учётные данные по умолчанию

После первого запуска создаётся администратор:
- **Логин**: `admin`
- **Пароль**: `admin123`

⚠️ Измените пароль в production!

## 🧪 Тестирование

```bash
# Запустить все тесты
python -m pytest tests/ -v

# С покрытием
python -m pytest tests/ -v --cov=app --cov-report=html
```

## 🛠 Разработка

### Добавить новый маршрут

1. Создайте функцию в `app/routes/main_routes.py`:
```python
@router.get("/new-page", response_class=HTMLResponse)
async def new_page(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse("new_page.html", {
        "request": request,
        "user": get_current_user_from_session(request)
    })
```

2. Создайте шаблон `templates/new_page.html`

### Добавить новую модель данных

1. Добавьте схему в `app/models/schemas.py`
2. Создайте таблицу в `app/database/db.py`
3. Реализуйте сервисные функции в `app/services/data_service.py`

## 📊 Функционал

- ✅ Регистрация и авторизация пользователей
- ✅ Геймификация (XP, уровни, достижения)
- ✅ Тесты с разными типами вопросов
- ✅ Словарь терминов
- ✅ Теоретические материалы
- ✅ Профиль пользователя со статистикой
- ✅ Админ-панель
- ✅ Тёмная тема
- ✅ Адаптивный дизайн

## 🔧 Конфигурация

Файл `.env`:
```env
SECRET_KEY=your-secret-key-min-32-chars
DEBUG=True
PORT=8000
TESTLEARN_DB=testlearn.db
```

## 📝 Лицензия

MIT License — см. файл LICENSE
