"""
Основные маршруты приложения
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.data_service import (
    get_all_categories, get_category_by_slug, get_topics_by_category,
    get_topic_by_id, get_all_quizzes, get_quiz_by_id, get_questions_by_quiz,
    save_quiz_result, get_all_glossary_terms, search_glossary,
    create_feedback, get_user_stats, add_xp, check_achievements,
    get_platform_stats
)
from app.database.db import get_db, DB_NAME
from app.deps.auth import generate_csrf_token, sanitize_input, validate_password
from app.services.user_service import get_current_user_from_session

router = APIRouter()


def setup_templates(static_path: str, templates_path: str) -> Jinja2Templates:
    """Настроить шаблоны."""
    return Jinja2Templates(directory=templates_path)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница."""
    templates = request.app.state.templates
    categories = get_all_categories()
    
    # Получаем статистику платформы
    stats = get_platform_stats()
    
    # Получаем пользователя если есть сессия
    user = get_current_user_from_session(request)
    user_stats = None
    if user:
        user_stats = get_user_stats(user.id)
    
    return templates.TemplateResponse(request, "index.html", {
        "categories": categories,
        "stats": stats,
        "user": user,
        "user_stats": user_stats,
        "csrf_token": generate_csrf_token()
    })


@router.get("/category/{slug}", response_class=HTMLResponse)
async def category_page(request: Request, slug: str):
    """Страница категории."""
    templates = request.app.state.templates
    category = get_category_by_slug(slug)
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    topics = get_topics_by_category(category.id)
    quizzes = get_all_quizzes()  # Можно фильтровать по категории
    
    user = get_current_user_from_session(request)
    
    return templates.TemplateResponse(request, "category.html", {
        "category": category,
        "topics": topics,
        "quizzes": quizzes,
        "user": user,
        "csrf_token": generate_csrf_token()
    })


@router.get("/theory/{topic_id}", response_class=HTMLResponse)
async def theory_page(request: Request, topic_id: int):
    """Страница теории."""
    templates = request.app.state.templates
    topic = get_topic_by_id(topic_id)
    
    if not topic:
        raise HTTPException(status_code=404, detail="Тема не найдена")
    
    user = get_current_user_from_session(request)
    
    # Получаем статистику для прогресс-бара
    total_topics = len(get_topics_by_category(topic.category_id))
    topics_read = 1  # Можно хранить в сессии или БД
    
    return templates.TemplateResponse(request, "theory.html", {
        "topic": topic,
        "user": user,
        "csrf_token": generate_csrf_token(),
        "total_topics": total_topics,
        "topics_read": topics_read
    })


@router.get("/quiz/{quiz_id}", response_class=HTMLResponse)
async def quiz_page(request: Request, quiz_id: int):
    """Страница теста."""
    templates = request.app.state.templates
    quiz = get_quiz_by_id(quiz_id)
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    questions = get_questions_by_quiz(quiz_id)
    user = get_current_user_from_session(request)
    
    return templates.TemplateResponse(request, "quiz.html", {
        "quiz": quiz,
        "questions": questions,
        "user": user,
        "csrf_token": generate_csrf_token()
    })


@router.post("/quiz/{quiz_id}/submit", response_class=HTMLResponse)
async def quiz_submit(request: Request, quiz_id: int):
    """Отправка результатов теста."""
    form = await request.form()
    quiz = get_quiz_by_id(quiz_id)

    if not quiz:
        raise HTTPException(status_code=404, detail="Тест не найден")

    questions = get_questions_by_quiz(quiz_id)
    score = 0
    total = len(questions)

    # Store user answers in session for later retrieval in results page
    for question in questions:
        user_answer = form.get(f"question_{question.id}")
        request.session[f"quiz_{quiz_id}_question_{question.id}"] = user_answer
        if user_answer == question.correct_option:
            score += 1

    user = get_current_user_from_session(request)
    user_id = user.id if user else None

    result_id = save_quiz_result(quiz_id, score, total, user_id)

    # Добавляем XP если пользователь авторизован
    if user:
        xp_gained = score * 10
        add_xp(user.id, xp_gained)
        check_achievements(user.id)

    return RedirectResponse(
        url=f"/quiz/{quiz_id}/result/{result_id}",
        status_code=303
    )


@router.get("/quiz/{quiz_id}/result/{result_id}", response_class=HTMLResponse)
async def quiz_result(request: Request, quiz_id: int, result_id: str):
    """Страница результатов теста."""
    templates = request.app.state.templates
    
    # Получаем результат теста по ID
    result = get_quiz_result_by_id(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Результат теста не найден")
    
    # Проверяем, что результат относится к данному тесту
    if result.quiz_id != quiz_id:
        raise HTTPException(status_code=400, detail="Результат не относится к данному тесту")
    
    quiz = get_quiz_by_id(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    questions = get_questions_by_quiz(quiz_id)
    
    # Подготавливаем детальные результаты для отображения
    detailed_results = []
    for question in questions:
        user_answer = request.session.get(f"quiz_{quiz_id}_question_{question.id}", "")
        is_correct = user_answer == question.correct_option
        
        detailed_results.append({
            "question": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "correct_answer": question.correct_option,
            "your_answer": user_answer,
            "is_correct": is_correct,
            "explanation": question.explanation
        })
    
    # Вычисляем процент
    percentage = int((result.score / result.total) * 100) if result.total > 0 else 0
    
    user = get_current_user_from_session(request)
    
    return templates.TemplateResponse(request, "quiz_result.html", {
        "quiz": quiz,
        "result": result,
        "results": detailed_results,
        "score": result.score,
        "total": result.total,
        "percentage": percentage,
        "user": user,
        "csrf_token": generate_csrf_token()
    })


@router.get("/glossary", response_class=HTMLResponse)
async def glossary_page(request: Request, q: str = ""):
    """Страница словаря."""
    templates = request.app.state.templates
    
    if q:
        terms = search_glossary(q)
    else:
        terms = get_all_glossary_terms()
    
    user = get_current_user_from_session(request)
    
    return templates.TemplateResponse(request, "glossary.html", {
        "terms": terms,
        "query": q,
        "user": user,
        "csrf_token": generate_csrf_token()
    })


@router.get("/feedback", response_class=HTMLResponse)
async def feedback_form(request: Request):
    """Форма обратной связи."""
    templates = request.app.state.templates
    user = get_current_user_from_session(request)
    
    # Получаем статистику отзывов
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(rating) FROM feedback WHERE rating > 0")
        avg_result = cursor.fetchone()[0]
        avg_rating = round(avg_result, 2) if avg_result else 0
        
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total_feedback = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT id, name, email, message, rating, created_at 
            FROM feedback 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        rows = cursor.fetchall()
        recent_feedback = [
            {"id": r[0], "name": r[1], "email": r[2], "message": r[3], "rating": r[4], "created_at": r[5]}
            for r in rows
        ]
    
    return templates.TemplateResponse(request, "feedback.html", {
        "user": user,
        "csrf_token": generate_csrf_token(),
        "avg_rating": avg_rating,
        "total_feedback": total_feedback,
        "recent_feedback": recent_feedback
    })


@router.post("/feedback", response_class=HTMLResponse)
async def feedback_submit(request: Request):
    """Отправка формы обратной связи."""
    form = await request.form()
    
    name = sanitize_input(form.get("name", ""), 100)
    email = sanitize_input(form.get("email", ""), 255)
    message = sanitize_input(form.get("message", ""), 2000)
    
    if not name or not message:
        raise HTTPException(status_code=400, detail="Имя и сообщение обязательны")
    
    create_feedback(name, message, email)
    
    return RedirectResponse(url="/feedback?success=1", status_code=303)


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Страница о проекте."""
    templates = request.app.state.templates
    user = get_current_user_from_session(request)
    
    return templates.TemplateResponse(request, "about.html", {
        "user": user,
        "csrf_token": generate_csrf_token()
    })


@router.get("/database", response_class=HTMLResponse)
async def database_page(request: Request):
    """Страница структуры БД."""
    templates = request.app.state.templates
    user = get_current_user_from_session(request)
    
    return templates.TemplateResponse(request, "database.html", {
        "user": user,
        "csrf_token": generate_csrf_token()
    })


@router.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Страница статистики."""
    templates = request.app.state.templates
    user = get_current_user_from_session(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    user_stats = get_user_stats(user.id)
    
    return templates.TemplateResponse(request, "stats.html", {
        "user": user,
        "user_stats": user_stats,
        "csrf_token": generate_csrf_token()
    })


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Страница профиля пользователя."""
    templates = request.app.state.templates
    user = get_current_user_from_session(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    user_stats = get_user_stats(user.id)
    
    return templates.TemplateResponse(request, "profile.html", {
        "user": user,
        "user_stats": user_stats,
        "csrf_token": generate_csrf_token()
    })


@router.get("/theory", response_class=HTMLResponse)
async def theory_list_page(request: Request):
    """Страница списка всех тем теории."""
    templates = request.app.state.templates
    categories = get_all_categories()
    user = get_current_user_from_session(request)
    
    # Собираем все темы из всех категорий
    all_topics = []
    for category in categories:
        topics = get_topics_by_category(category.id)
        for topic in topics:
            all_topics.append({
                'id': topic.id,
                'title': topic.title,
                'content': topic.content if hasattr(topic, 'content') else '',
                'category_name': category.name,
                'category_slug': category.slug,
                'created_at': topic.created_at if hasattr(topic, 'created_at') else None
            })
    
    return templates.TemplateResponse(request, "theory_list.html", {
        "topics": all_topics,
        "categories": categories,
        "user": user,
        "csrf_token": generate_csrf_token()
    })


@router.get("/quiz", response_class=HTMLResponse)
async def quiz_list_page(request: Request):
    """Страница списка всех тестов."""
    templates = request.app.state.templates
    quizzes = get_all_quizzes()
    user = get_current_user_from_session(request)
    
    return templates.TemplateResponse(request, "quiz_list.html", {
        "quizzes": quizzes,
        "user": user,
        "csrf_token": generate_csrf_token()
    })


@router.get("/bookmarks", response_class=HTMLResponse)
async def bookmarks_page(request: Request):
    """Страница закладок пользователя."""
    templates = request.app.state.templates
    user = get_current_user_from_session(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Получаем закладки пользователя из БД
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.id, b.topic_id, b.quiz_id, b.created_at,
                   t.title as topic_title, q.title as quiz_title
            FROM bookmarks b
            LEFT JOIN topics t ON b.topic_id = t.id
            LEFT JOIN quizzes q ON b.quiz_id = q.id
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC
        """, (user.id,))
        rows = cursor.fetchall()
        bookmarks = [
            {
                "id": r[0],
                "topic_id": r[1],
                "quiz_id": r[2],
                "created_at": r[3],
                "topic_title": r[4],
                "quiz_title": r[5]
            }
            for r in rows
        ]
    
    return templates.TemplateResponse(request, "bookmarks.html", {
        "bookmarks": bookmarks,
        "user": user,
        "csrf_token": generate_csrf_token()
    })
