""" Маршруты админ-панели """
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import secrets
from app.deps.auth import (
    get_current_admin,
    create_admin_session,
    generate_csrf_token
)
from app.services.data_service import (
    create_category, update_category, delete_category,
    get_all_categories, get_category_by_id, get_category_by_slug,
    create_topic, update_topic, delete_topic,
    get_topics_by_category, get_topic_by_id,
    create_quiz, get_all_quizzes, get_quiz_by_id,
    create_question, update_question, delete_question,
    get_questions_by_quiz, get_question_by_id,
    get_all_feedback,
    get_all_glossary_terms, search_glossary,
    get_glossary_by_letter, get_glossary_by_id,
    create_glossary_term, update_glossary_term, delete_glossary_term
)
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD

router = APIRouter(prefix="/admin", tags=["admin"])


def _add_topic_count_to_categories(categories):
    """Add topic_count attribute to each category."""
    for category in categories:
        topics = get_topics_by_category(category.id)
        category.topic_count = len(topics)
    return categories


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin: bool = Depends(get_current_admin)):
    """Панель администратора."""
    templates = request.app.state.templates
    categories = _add_topic_count_to_categories(get_all_categories())
    quizzes = get_all_quizzes()
    feedbacks = get_all_feedback()
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    return templates.TemplateResponse(request, "admin/dashboard.html", {
        "categories": categories,
        "quizzes": quizzes,
        "feedbacks": feedbacks,
        "csrf_token": csrf_token
    })


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Страница входа администратора."""
    templates = request.app.state.templates
    from app.deps.auth import verify_admin_session
    if verify_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)
    csrf_token = request.session.get("csrf_token")
    if not csrf_token:
        csrf_token = generate_csrf_token()
        request.session["csrf_token"] = csrf_token
    return templates.TemplateResponse(request, "admin/login.html", {
        "error": None,
        "csrf_token": csrf_token
    })


@router.post("/login", response_class=HTMLResponse)
async def admin_login_submit(request: Request):
    """Обработка входа администратора."""
    templates = request.app.state.templates
    form = await request.form()
    # Валидация CSRF токена
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        return templates.TemplateResponse(request, "admin/login.html", {
            "error": "Ошибка безопасности: неверный CSRF токен. Пожалуйста, обновите страницу и попробуйте снова.",
            "csrf_token": generate_csrf_token()
        })
    username = form.get("username", "").strip()
    password = form.get("password", "")
    # Проверяем учётные данные через config
    if username != ADMIN_USERNAME:
        return templates.TemplateResponse(request, "admin/login.html", {
            "error": "Неверное имя пользователя или пароль",
            "csrf_token": generate_csrf_token()
        })
    if password != ADMIN_PASSWORD:
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
    request: Request, admin: bool = Depends(get_current_admin)
):
    """Создание категории."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
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
    request: Request, admin: bool = Depends(get_current_admin)
):
    """Создание темы."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
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
    request: Request, admin: bool = Depends(get_current_admin)
):
    """Создание теста."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
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
    request: Request, admin: bool = Depends(get_current_admin)
):
    """Создание вопроса."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
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
        quiz_id=quiz_id, question_text=question_text,
        option_a=option_a, option_b=option_b,
        option_c=option_c, option_d=option_d,
        correct_option=correct_option, explanation=explanation,
        order_num=order_num
    )
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании вопроса")
    return RedirectResponse(url="/admin", status_code=303)


# ====== ADMIN API ENDPOINTS ======

@router.get("/api/categories", response_class=JSONResponse)
async def api_admin_categories(request: Request, admin: bool = Depends(get_current_admin)):
    """Получить список всех категорий для админ-панели."""
    categories = get_all_categories()
    categories_data = [
        {"id": cat.id, "name": cat.name, "slug": cat.slug,
         "description": cat.description, "icon": cat.icon}
        for cat in categories
    ]
    return JSONResponse(content=categories_data)


@router.post("/api/categories", response_class=JSONResponse)
async def api_admin_create_category(request: Request, admin: bool = Depends(get_current_admin)):
    """Создать новую категорию через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    name = form.get("name", "").strip()
    slug = form.get("slug", "").strip()
    description = form.get("description", "").strip()
    icon = form.get("icon", "check-circle")
    if not name or not slug:
        raise HTTPException(status_code=400, detail="Название и slug обязательны")
    success = create_category(name, slug, description, icon)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании категории")
    category = get_category_by_slug(slug)
    if category:
        category_data = {
            "id": category.id, "name": category.name, "slug": category.slug,
            "description": category.description, "icon": category.icon
        }
        return JSONResponse(content=category_data)
    return JSONResponse(content={"name": name, "slug": slug})


@router.put("/api/categories/{category_id}", response_class=JSONResponse)
async def api_admin_update_category(request: Request, category_id: int, admin: bool = Depends(get_current_admin)):
    """Обновить категорию через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    name = form.get("name", "").strip()
    slug = form.get("slug", "").strip()
    description = form.get("description", "").strip()
    icon = form.get("icon", "check-circle")
    if not name or not slug:
        raise HTTPException(status_code=400, detail="Название и slug обязательны")
    success = update_category(category_id, name, slug, description, icon)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при обновлении категории")
    category = get_category_by_id(category_id)
    if category:
        category_data = {
            "id": category.id, "name": category.name, "slug": category.slug,
            "description": category.description, "icon": category.icon
        }
        return JSONResponse(content=category_data)
    raise HTTPException(status_code=404, detail="Категория не найдена")


@router.delete("/api/categories/{category_id}", response_class=JSONResponse)
async def api_admin_delete_category(request: Request, category_id: int, admin: bool = Depends(get_current_admin)):
    """Удалить категорию через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    success = delete_category(category_id)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при удалении категории")
    return JSONResponse(content={"message": "Категория успешно удалена"})


@router.get("/api/topics", response_class=JSONResponse)
async def api_admin_topics(request: Request, admin: bool = Depends(get_current_admin)):
    """Получить список всех тем для админ-панели."""
    category_id = request.query_params.get('category_id')
    if category_id:
        topics = get_topics_by_category(int(category_id))
    else:
        topics = []
        categories = get_all_categories()
        for cat in categories:
            topics.extend(get_topics_by_category(cat.id))
    topics_data = []
    for topic in topics:
        cat = get_category_by_id(topic.category_id) if topic.category_id else None
        topics_data.append({
            "id": topic.id, "category_id": topic.category_id,
            "title": topic.title, "content": topic.content,
            "order_num": topic.order_num,
            "category_name": cat.name if cat else None
        })
    return JSONResponse(content=topics_data)


@router.post("/api/topics", response_class=JSONResponse)
async def api_admin_create_topic(request: Request, admin: bool = Depends(get_current_admin)):
    """Создать новую тему через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    category_id = int(form.get("category_id", 0))
    title = form.get("title", "").strip()
    content = form.get("content", "").strip()
    order_num = int(form.get("order_num", 0))
    if not category_id or not title or not content:
        raise HTTPException(status_code=400, detail="Все поля обязательны")
    success = create_topic(category_id, title, content, order_num)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании темы")
    # Находим созданную тему по заголовку в категории
    topics = get_topics_by_category(category_id)
    topic = None
    for t in topics:
        if t.title == title:
            topic = t
            break
    if topic:
        topic_data = {
            "id": topic.id, "category_id": topic.category_id,
            "title": topic.title, "content": topic.content,
            "order_num": topic.order_num
        }
        return JSONResponse(content=topic_data)
    return JSONResponse(content={"category_id": category_id, "title": title, "content": content, "order_num": order_num})


@router.put("/api/topics/{topic_id}", response_class=JSONResponse)
async def api_admin_update_topic(request: Request, topic_id: int, admin: bool = Depends(get_current_admin)):
    """Обновить тему через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    category_id = int(form.get("category_id", 0))
    title = form.get("title", "").strip()
    content = form.get("content", "").strip()
    order_num = int(form.get("order_num", 0))
    if not category_id or not title or not content:
        raise HTTPException(status_code=400, detail="Все поля обязательны")
    success = update_topic(topic_id, category_id, title, content, order_num)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при обновлении темы")
    topic = get_topic_by_id(topic_id)
    if topic:
        topic_data = {
            "id": topic.id, "category_id": topic.category_id,
            "title": topic.title, "content": topic.content,
            "order_num": topic.order_num
        }
        return JSONResponse(content=topic_data)
    raise HTTPException(status_code=404, detail="Тема не найдена")


@router.delete("/api/topics/{topic_id}", response_class=JSONResponse)
async def api_admin_delete_topic(request: Request, topic_id: int, admin: bool = Depends(get_current_admin)):
    """Удалить тему через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    success = delete_topic(topic_id)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при удалении темы")
    return JSONResponse(content={"message": "Тема успешно удалена"})


# ====== GLOSSARY API ENDPOINTS ======

@router.get("/api/glossary", response_class=JSONResponse)
async def api_admin_glossary(request: Request, admin: bool = Depends(get_current_admin)):
    """Получить список всех терминов глоссария для админ-панели."""
    letter = request.query_params.get('letter')
    search = request.query_params.get('search')
    if letter:
        terms = get_glossary_by_letter(letter)
    elif search:
        terms = search_glossary(search)
    else:
        terms = get_all_glossary_terms()
    terms_data = [
        {"id": term.id, "term": term.term, "definition": term.definition, "letter": term.letter}
        for term in terms
    ]
    return JSONResponse(content=terms_data)


@router.post("/api/glossary", response_class=JSONResponse)
async def api_admin_create_glossary_term(request: Request, admin: bool = Depends(get_current_admin)):
    """Создать новый термин глоссария через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    term = form.get("term", "").strip()
    definition = form.get("definition", "").strip()
    letter = form.get("letter", "").strip().upper()
    if not term or not definition:
        raise HTTPException(status_code=400, detail="Термин и определение обязательны")
    if not letter and term:
        letter = term[0].upper()
    if len(letter) != 1 or not letter.isalpha():
        raise HTTPException(status_code=400, detail="Буква должна быть одним символом")
    success = create_glossary_term(term, definition, letter)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании термина")
    # Находим созданный термин
    terms = get_all_glossary_terms()
    created_term = None
    for t in terms:
        if t.term == term:
            created_term = t
            break
    if created_term:
        return JSONResponse(content={
            "id": created_term.id, "term": created_term.term,
            "definition": created_term.definition, "letter": created_term.letter
        })
    return JSONResponse(content={"term": term, "definition": definition, "letter": letter})


@router.put("/api/glossary/{term_id}", response_class=JSONResponse)
async def api_admin_update_glossary_term(request: Request, term_id: int, admin: bool = Depends(get_current_admin)):
    """Обновить термин глоссария через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    term = form.get("term", "").strip()
    definition = form.get("definition", "").strip()
    letter = form.get("letter", "").strip().upper()
    if not term or not definition:
        raise HTTPException(status_code=400, detail="Термин и определение обязательны")
    if not letter and term:
        letter = term[0].upper()
    if len(letter) != 1 or not letter.isalpha():
        raise HTTPException(status_code=400, detail="Буква должна быть одним символом")
    success = update_glossary_term(term_id, term, definition, letter)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при обновлении термина")
    term_obj = get_glossary_by_id(term_id)
    if term_obj:
        return JSONResponse(content={
            "id": term_obj.id, "term": term_obj.term,
            "definition": term_obj.definition, "letter": term_obj.letter
        })
    raise HTTPException(status_code=404, detail="Термин не найден")


@router.delete("/api/glossary/{term_id}", response_class=JSONResponse)
async def api_admin_delete_glossary_term(request: Request, term_id: int, admin: bool = Depends(get_current_admin)):
    """Удалить термин глоссария через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    success = delete_glossary_term(term_id)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при удалении термина")
    return JSONResponse(content={"message": "Термин успешно удален"})


# ====== QUESTIONS API ENDPOINTS ======

@router.get("/api/questions", response_class=JSONResponse)
async def api_admin_questions(request: Request, admin: bool = Depends(get_current_admin)):
    """Получить список всех вопросов для админ-панели."""
    quiz_id = request.query_params.get('quiz_id')
    if quiz_id:
        questions = get_questions_by_quiz(int(quiz_id))
    else:
        questions = []
        quizzes = get_all_quizzes()
        for quiz in quizzes:
            questions.extend(get_questions_by_quiz(quiz.id))
    questions_data = []
    for question in questions:
        quiz_obj = get_quiz_by_id(question.quiz_id)
        quiz_title = quiz_obj.title if quiz_obj else ""
        questions_data.append({
            "id": question.id, "quiz_id": question.quiz_id,
            "quiz_title": quiz_title,
            "question_text": question.question_text,
            "option_a": question.option_a, "option_b": question.option_b,
            "option_c": question.option_c, "option_d": question.option_d,
            "correct_option": question.correct_option,
            "explanation": question.explanation,
            "order_num": question.order_num
        })
    return JSONResponse(content=questions_data)


@router.post("/api/questions", response_class=JSONResponse)
async def api_admin_create_question(request: Request, admin: bool = Depends(get_current_admin)):
    """Создать новый вопрос через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    quiz_id = int(form.get("quiz_id", 0))
    question_text = form.get("question_text", "").strip()
    option_a = form.get("option_a", "").strip()
    option_b = form.get("option_b", "").strip()
    option_c = form.get("option_c", "").strip()
    option_d = form.get("option_d", "").strip()
    correct_option = form.get("correct_option", "").strip()
    explanation = form.get("explanation", "").strip()
    order_num = int(form.get("order_num", 0))
    if not quiz_id or not question_text or not option_a or not option_b or not option_c or not option_d or not correct_option:
        raise HTTPException(status_code=400, detail="Все поля обязательны")
    if correct_option not in ("A", "B", "C", "D"):
        raise HTTPException(status_code=400, detail="Правильный вариант должен быть A, B, C или D")
    success = create_question(
        quiz_id=quiz_id, question_text=question_text,
        option_a=option_a, option_b=option_b,
        option_c=option_c, option_d=option_d,
        correct_option=correct_option, explanation=explanation,
        order_num=order_num
    )
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при создании вопроса")
    # Находим последний созданный вопрос для этой викторины
    questions = get_questions_by_quiz(quiz_id)
    created_question = max(questions, key=lambda q: q.id) if questions else None
    if created_question:
        quiz_obj = get_quiz_by_id(created_question.quiz_id)
        quiz_title = quiz_obj.title if quiz_obj else ""
        return JSONResponse(content={
            "id": created_question.id, "quiz_id": created_question.quiz_id,
            "quiz_title": quiz_title,
            "question_text": created_question.question_text,
            "option_a": created_question.option_a, "option_b": created_question.option_b,
            "option_c": created_question.option_c, "option_d": created_question.option_d,
            "correct_option": created_question.correct_option,
            "explanation": created_question.explanation,
            "order_num": created_question.order_num
        })
    quiz_obj = get_quiz_by_id(quiz_id)
    quiz_title = quiz_obj.title if quiz_obj else ""
    return JSONResponse(content={
        "quiz_id": quiz_id, "quiz_title": quiz_title,
        "question_text": question_text,
        "option_a": option_a, "option_b": option_b,
        "option_c": option_c, "option_d": option_d,
        "correct_option": correct_option,
        "explanation": explanation, "order_num": order_num
    })


@router.put("/api/questions/{question_id}", response_class=JSONResponse)
async def api_admin_update_question(request: Request, question_id: int, admin: bool = Depends(get_current_admin)):
    """Обновить вопрос через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    quiz_id = int(form.get("quiz_id", 0))
    question_text = form.get("question_text", "").strip()
    option_a = form.get("option_a", "").strip()
    option_b = form.get("option_b", "").strip()
    option_c = form.get("option_c", "").strip()
    option_d = form.get("option_d", "").strip()
    correct_option = form.get("correct_option", "").strip()
    explanation = form.get("explanation", "").strip()
    order_num = int(form.get("order_num", 0))
    if not quiz_id or not question_text or not option_a or not option_b or not option_c or not option_d or not correct_option:
        raise HTTPException(status_code=400, detail="Все поля обязательны")
    if correct_option not in ("A", "B", "C", "D"):
        raise HTTPException(status_code=400, detail="Правильный вариант должен быть A, B, C или D")
    success = update_question(question_id, quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation, order_num)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при обновлении вопроса")
    question_obj = get_question_by_id(question_id)
    if question_obj:
        quiz_obj = get_quiz_by_id(question_obj.quiz_id)
        quiz_title = quiz_obj.title if quiz_obj else ""
        return JSONResponse(content={
            "id": question_obj.id, "quiz_id": question_obj.quiz_id,
            "quiz_title": quiz_title,
            "question_text": question_obj.question_text,
            "option_a": question_obj.option_a, "option_b": question_obj.option_b,
            "option_c": question_obj.option_c, "option_d": question_obj.option_d,
            "correct_option": question_obj.correct_option,
            "explanation": question_obj.explanation,
            "order_num": question_obj.order_num
        })
    raise HTTPException(status_code=404, detail="Вопрос не найден")


@router.delete("/api/questions/{question_id}", response_class=JSONResponse)
async def api_admin_delete_question(request: Request, question_id: int, admin: bool = Depends(get_current_admin)):
    """Удалить вопрос через API."""
    form = await request.form()
    csrf_token = form.get("csrf_token")
    stored_token = request.session.get("csrf_token")
    if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")
    success = delete_question(question_id)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при удалении вопроса")
    return JSONResponse(content={"message": "Вопрос успешно удален"})
