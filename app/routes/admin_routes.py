"""
Маршруты админ-панели
"""

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import os

from app.deps.auth import (
    get_current_admin, create_admin_session, 
    verify_password, get_admin_password_hash,
    generate_csrf_token
)
from app.services.data_service import (
    create_category, create_topic, create_quiz, create_question,
    get_all_categories, get_all_quizzes, get_all_feedback
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin: bool = Depends(get_current_admin)):
    """Панель администратора."""
    templates = request.app.state.templates
    
    categories = get_all_categories()
    quizzes = get_all_quizzes()
    feedbacks = get_all_feedback()
    
    return templates.TemplateResponse(request, "admin/dashboard.html", {
        "categories": categories,
        "quizzes": quizzes,
        "feedbacks": feedbacks,
        "csrf_token": generate_csrf_token()
    })


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Страница входа администратора."""
    templates = request.app.state.templates
    
    # Проверяем, есть ли активная сессия
    from app.deps.auth import verify_admin_session
    if verify_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)
    
    return templates.TemplateResponse(request, "admin/login.html", {
        "error": None,
        "csrf_token": generate_csrf_token()
    })


@router.post("/login", response_class=HTMLResponse)
async def admin_login_submit(request: Request):
    """Обработка входа администратора."""
    templates = request.app.state.templates
    form = await request.form()
    
    username = form.get("username", "").strip()
    password = form.get("password", "")
    
    # Проверяем учётные данные
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    
    if username != admin_username:
        return templates.TemplateResponse(request, "admin/login.html", {
            "error": "Неверное имя пользователя или пароль",
            "csrf_token": generate_csrf_token()
        })
    
    # Для простоты проверяем пароль напрямую (в продакшене использовать хеш)
    expected_password = os.getenv("ADMIN_PASSWORD", "admin")
    
    if password != expected_password:
        return templates.TemplateResponse(request, "admin/login.html", {
            "error": "Неверное имя пользователя или пароль",
            "csrf_token": generate_csrf_token()
        })
    
    # Создаём сессию
    session_id = create_admin_session(username)
    
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(key="admin_session", value=session_id, httponly=True, max_age=86400)
    return response


@router.get("/logout", response_class=HTMLResponse)
async def admin_logout(request: Request):
    """Выход администратора."""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


@router.post("/category/create", response_class=HTMLResponse)
async def create_category_route(
    request: Request,
    admin: bool = Depends(get_current_admin)
):
    """Создание категории."""
    form = await request.form()
    
    name = form.get("name", "").strip()
    slug = form.get("slug", "").strip()
    description = form.get("description", "").strip()
    icon = form.get("icon", "check-circle")
    
    if not name or not slug:
        raise HTTPException(status_code=400, detail="Название и slug обязательны")
    
    success = create_category(name, slug, description, icon)
    
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании категории")
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/topic/create", response_class=HTMLResponse)
async def create_topic_route(
    request: Request,
    admin: bool = Depends(get_current_admin)
):
    """Создание темы."""
    form = await request.form()
    
    category_id = int(form.get("category_id", 0))
    title = form.get("title", "").strip()
    content = form.get("content", "").strip()
    order_num = int(form.get("order_num", 0))
    
    if not category_id or not title or not content:
        raise HTTPException(status_code=400, detail="Все поля обязательны")
    
    success = create_topic(category_id, title, content, order_num)
    
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании темы")
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/quiz/create", response_class=HTMLResponse)
async def create_quiz_route(
    request: Request,
    admin: bool = Depends(get_current_admin)
):
    """Создание теста."""
    form = await request.form()
    
    category_id = form.get("category_id")
    category_id = int(category_id) if category_id else None
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    
    if not title:
        raise HTTPException(status_code=400, detail="Название обязательно")
    
    success = create_quiz(category_id, title, description)
    
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании теста")
    
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/question/create", response_class=HTMLResponse)
async def create_question_route(
    request: Request,
    admin: bool = Depends(get_current_admin)
):
    """Создание вопроса."""
    form = await request.form()
    
    quiz_id = int(form.get("quiz_id", 0))
    question_text = form.get("question_text", "").strip()
    option_a = form.get("option_a", "").strip()
    option_b = form.get("option_b", "").strip()
    option_c = form.get("option_c", "").strip()
    option_d = form.get("option_d", "").strip()
    correct_option = form.get("correct_option", "").strip()
    explanation = form.get("explanation", "").strip()
    order_num = int(form.get("order_num", 0))
    
    if not quiz_id or not question_text or not correct_option:
        raise HTTPException(status_code=400, detail="Обязательные поля не заполнены")
    
    success = create_question(
        quiz_id=quiz_id,
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option,
        explanation=explanation,
        order_num=order_num
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании вопроса")
    
    return RedirectResponse(url="/admin", status_code=303)
