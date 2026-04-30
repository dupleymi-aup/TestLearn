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


def _process_question(question, form_data):
    """Обрабатывает один вопрос и возвращает (балл, ответ пользователя)."""
    # Получаем все значения для этого вопроса (может быть несколько для multiple_choice)
    all_values = form_data.getlist(f"question_{question.id}")

    if question.question_type == "multiple_choice":
        # Для множественного выбора - ответ это список выбранных вариантов
        user_answer = ",".join(sorted(all_values)) if all_values else ""
        # Правильный ответ тоже может быть списком (например "A,B,D")
        correct_answers = sorted(question.correct_option.split(","))
        user_answers_list = sorted(user_answer.split(",")) if user_answer else []
        # Ответ считается правильным только если все выбранные варианты совпадают с правильными
        if user_answers_list == correct_answers:
            return 1, user_answer
        return 0, user_answer

    elif question.question_type == "matching":
        # Для вопросов на сопоставление - проверяем каждую пару
        matching_correct = 0
        matching_total = len(question.matching_pairs) if question.matching_pairs else 0
        user_matching_answers = {}

        for i, pair in enumerate(question.matching_pairs or []):
            user_match = form_data.get(f"match_{question.id}_{i}", "")
            user_matching_answers[f"match_{i}"] = user_match
            if user_match == pair["right"]:
                matching_correct += 1

        # Вопрос считается правильным если все пары сопоставлены верно
        if matching_correct == matching_total and matching_total > 0:
            return 1, ",".join([f"{k}:{v}" for k, v in user_matching_answers.items()])
        return 0, ",".join([f"{k}:{v}" for k, v in user_matching_answers.items()])

    elif question.question_type == "ordering":
        # Для вопросов на упорядочивание - сравниваем порядок
        user_order_str = all_values[0] if all_values else ""
        user_order = user_order_str.split("|") if user_order_str else []

        # Получаем правильный порядок
        correct_order = [item["text"] for item in sorted(question.ordering_items or [], key=lambda x: x["order"])]

        # Сравниваем порядок
        if user_order == correct_order and len(user_order) == len(correct_order):
            return 1, user_order_str
        return 0, user_order_str

    elif question.question_type == "text_input":
        # Для текстового ввода - сравниваем строку (без учета регистра и пробелов по краям)
        user_answer = all_values[0].strip().lower() if all_values else ""
        expected = (question.expected_answer or "").strip().lower()
        if user_answer == expected:
            return 1, all_values[0] if all_values else ""  # Возвращаем оригинальный ответ для отображения
        return 0, all_values[0] if all_values else ""

    else:
        # Для одиночного выбора - просто сравниваем строки
        user_answer = all_values[0] if all_values else ""
        if user_answer == question.correct_option:
            return 1, user_answer
        return 0, user_answer


def _build_question_detail(question, user_answer_raw):
    """Строит детали для одного вопроса."""
    if question.question_type == "multiple_choice":
        correct_answers = sorted(question.correct_option.split(","))
        user_answers_list = sorted(user_answer_raw.split(",")) if user_answer_raw else []
        is_correct = user_answers_list == correct_answers

        return {
            "question": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "correct_answer": question.correct_option,
            "your_answer": user_answer_raw,
            "is_correct": is_correct,
            "explanation": question.explanation,
            "question_type": question.question_type
        }

    elif question.question_type == "matching":
        # Парсим ответы пользователя для matching
        user_matching = {}
        if user_answer_raw:
            for pair_str in user_answer_raw.split(","):
                if ":" in pair_str:
                    key, value = pair_str.split(":", 1)
                    user_matching[key] = value

        # Проверяем каждую пару
        matching_results = []
        all_correct = True
        for i, pair in enumerate(question.matching_pairs or []):
            user_match = user_matching.get(f"match_{i}", "")
            is_pair_correct = user_match == pair["right"]
            if not is_pair_correct:
                all_correct = False
            matching_results.append({
                "left": pair["left"],
                "correct_right": pair["right"],
                "user_right": user_match,
                "is_correct": is_pair_correct
            })

        return {
            "question": question.question_text,
            "correct_answer": "Все пары верно",
            "your_answer": "См. детали",
            "is_correct": all_correct,
            "explanation": question.explanation,
            "question_type": question.question_type,
            "matching_results": matching_results
        }

    elif question.question_type == "ordering":
        # Для вопросов на упорядочивание
        correct_order = [item["text"] for item in sorted(question.ordering_items or [], key=lambda x: x["order"])]
        user_order = user_answer_raw.split("|") if user_answer_raw else []
        is_correct = user_order == correct_order and len(user_order) == len(correct_order)

        # Формируем детали для отображения
        ordering_results = []
        for i, item_text in enumerate(correct_order):
            user_item = user_order[i] if i < len(user_order) else ""
            ordering_results.append({
                "item": item_text,
                "user_item": user_item,
                "position": i + 1,
                "is_correct": user_item == item_text
            })

        return {
            "question": question.question_text,
            "correct_answer": " | ".join(correct_order),
            "your_answer": " | ".join(user_order) if user_order else "(не дано)",
            "is_correct": is_correct,
            "explanation": question.explanation,
            "question_type": question.question_type,
            "ordering_results": ordering_results
        }

    elif question.question_type == "text_input":
        # Для текстового ввода
        expected = (question.expected_answer or "").strip().lower()
        user_answer_stripped = user_answer_raw.strip().lower()
        is_correct = user_answer_stripped == expected

        return {
            "question": question.question_text,
            "expected_answer": question.expected_answer,
            "your_answer": user_answer_raw,
            "is_correct": is_correct,
            "explanation": question.explanation,
            "question_type": question.question_type
        }

    else:
        # Для одиночного выбора
        is_correct = user_answer_raw == question.correct_option
        return {
            "question": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "correct_answer": question.correct_option,
            "your_answer": user_answer_raw,
            "is_correct": is_correct,
            "explanation": question.explanation,
            "question_type": question.question_type
        }


def _get_quiz_result(result_id: str):
    """Получить результат теста по ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, quiz_id, score, total, created_at, user_id
            FROM quiz_results
            WHERE id = ?
        """, (result_id,))
        row = cursor.fetchone()

        if not row:
            return None
        return {
            "id": row[0],
            "quiz_id": row[1],
            "score": row[2],
            "total": row[3],
            "created_at": row[4],
            "user_id": row[5]
        }


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
    
    # Устанавливаем лимит времени по умолчанию (10 минут)
    time_limit = getattr(quiz, 'time_limit', 600) or 600
    
    return templates.TemplateResponse(request, "quiz.html", {
        "quiz": quiz,
        "questions": questions,
        "user": user,
        "csrf_token": generate_csrf_token(),
        "time_limit": time_limit
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

    # Собираем ответы для передачи на страницу результатов
    user_answers = {}

    for question in questions:
        score_inc, user_answer = _process_question(question, form)
        score += score_inc
        user_answers[question.id] = user_answer

    user = get_current_user_from_session(request)
    user_id = user.id if user else None

    result_id = save_quiz_result(quiz_id, score, total, user_id)

    # Добавляем XP если пользователь авторизован
    if user:
        xp_gained = score * 10
        add_xp(user.id, xp_gained)
        check_achievements(user.id)

    # Перенаправляем с ответами как query параметры
    query_params = "&".join([f"q{qid}={ans}" for qid, ans in user_answers.items()])
    return RedirectResponse(
        url=f"/quiz/{quiz_id}/result/{result_id}?{query_params}",
        status_code=303
    )


@router.get("/quiz/{quiz_id}/result/{result_id}", response_class=HTMLResponse)
async def quiz_result(request: Request, quiz_id: int, result_id: str):
    """Страница результатов теста."""
    templates = request.app.state.templates

    # Получаем результат теста
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, quiz_id, score, total, created_at, user_id
            FROM quiz_results
            WHERE id = ?
        """, (result_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Результат не найден")

        result = {
            "id": row[0],
            "quiz_id": row[1],
            "score": row[2],
            "total": row[3],
            "created_at": row[4],
            "user_id": row[5]
        }

    quiz = get_quiz_by_id(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Тест не найден")

    questions = get_questions_by_quiz(quiz_id)
    user = get_current_user_from_session(request)

    def _build_question_detail(question, user_answer_raw):
        """Строит детали для одного вопроса."""
        if question.question_type == "multiple_choice":
            correct_answers = sorted(question.correct_option.split(","))
            user_answers_list = sorted(user_answer_raw.split(",")) if user_answer_raw else []
            is_correct = user_answers_list == correct_answers

            return {
                "question": question.question_text,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct_answer": question.correct_option,
                "your_answer": user_answer_raw,
                "is_correct": is_correct,
                "explanation": question.explanation,
                "question_type": question.question_type
            }

        elif question.question_type == "matching":
            # Парсим ответы пользователя для matching
            user_matching = {}
            if user_answer_raw:
                for pair_str in user_answer_raw.split(","):
                    if ":" in pair_str:
                        key, value = pair_str.split(":", 1)
                        user_matching[key] = value

            # Проверяем каждую пару
            matching_results = []
            all_correct = True
            for i, pair in enumerate(question.matching_pairs or []):
                user_match = user_matching.get(f"match_{i}", "")
                is_pair_correct = user_match == pair["right"]
                if not is_pair_correct:
                    all_correct = False
                matching_results.append({
                    "left": pair["left"],
                    "correct_right": pair["right"],
                    "user_right": user_match,
                    "is_correct": is_pair_correct
                })

            return {
                "question": question.question_text,
                "correct_answer": "Все пары верно",
                "your_answer": "См. детали",
                "is_correct": all_correct,
                "explanation": question.explanation,
                "question_type": question.question_type,
                "matching_results": matching_results
            }

        elif question.question_type == "ordering":
            # Парсим порядок пользователя
            user_order = user_answer_raw.split("|") if user_answer_raw else []

            # Получаем правильный порядок
            correct_order = [item["text"] for item in sorted(question.ordering_items or [], key=lambda x: x["order"])]

            # Сравниваем
            is_correct = user_order == correct_order and len(user_order) == len(correct_order)

            # Формируем детали для отображения
            ordering_results = []
            for i, item_text in enumerate(correct_order):
                user_item = user_order[i] if i < len(user_order) else ""
                ordering_results.append({
                    "item": item_text,
                    "user_item": user_item,
                    "position": i + 1,
                    "is_correct": user_item == item_text
                })

            return {
                "question": question.question_text,
                "correct_answer": " | ".join(correct_order),
                "your_answer": " | ".join(user_order) if user_order else "(не дано)",
                "is_correct": is_correct,
                "explanation": question.explanation,
                "question_type": question.question_type,
                "ordering_results": ordering_results
            }
        else:
            # Для одиночного выбора
            is_correct = user_answer_raw == question.correct_option

            return {
                "question": question.question_text,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct_answer": question.correct_option,
                "your_answer": user_answer_raw,
                "is_correct": is_correct,
                "explanation": question.explanation,
                "question_type": question.question_type
            }

    # Формируем детальные результаты по каждому вопросу
    results_detail = []
    for question in questions:
        user_answer_raw = request.query_params.get(f"q{question.id}", "")
        results_detail.append(_build_question_detail(question, user_answer_raw))

    percentage = round((result["score"] / result["total"]) * 100) if result["total"] > 0 else 0

    return templates.TemplateResponse(request, "quiz_result.html", {
        "quiz": quiz,
        "result": result,
        "score": result["score"],
        "total": result["total"],
        "percentage": percentage,
        "results": results_detail,
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
    
    # Получаем достижения пользователя с информацией из таблицы achievements
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT ua.earned_at, a.name, a.description, a.icon
            FROM user_achievements ua
            JOIN achievements a ON ua.achievement_id = a.id
            WHERE ua.user_id = ?
            ORDER BY ua.earned_at DESC
        """, (user.id,))
        rows = cursor.fetchall()
        achievements = [
            {
                "name": r[1],
                "description": r[2],
                "icon": r[3] or "🏆",
                "earned_at": r[0]
            }
            for r in rows
        ]
        
        # Получаем историю прохождений тестов
        cursor.execute("""
            SELECT qr.id, qr.quiz_id, qr.score, qr.total, qr.created_at, q.title as quiz_title
            FROM quiz_results qr
            JOIN quizzes q ON qr.quiz_id = q.id
            WHERE qr.user_id = ?
            ORDER BY qr.created_at DESC
            LIMIT 10
        """, (user.id,))
        rows = cursor.fetchall()
        quiz_history = [
            {
                "id": r[0],
                "quiz_id": r[1],
                "score": r[2],
                "total": r[3],
                "created_at": r[4],
                "quiz_title": r[5],
                "percentage": round((r[2] / r[3]) * 100) if r[3] > 0 else 0
            }
            for r in rows
        ]
    
    return templates.TemplateResponse(request, "profile.html", {
        "user": user,
        "user_stats": user_stats,
        "achievements": achievements,
        "quiz_history": quiz_history,
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
