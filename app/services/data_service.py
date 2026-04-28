"""
Сервисы для работы с данными
"""

import uuid
from datetime import datetime
from typing import Optional, List, Tuple

from app.database.db import get_db
from app.models.schemas import (
    Category, Topic, Quiz, Question, QuizResult,
    GlossaryTerm, Feedback, User, Achievement, UserAchievement, UserXP
)
from app.deps.auth import hash_password, validate_username, validate_email


# ====== КАТЕГОРИИ ======

def get_all_categories() -> List[Category]:
    """Получить все категории."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM categories ORDER BY id")
        rows = cursor.fetchall()
        return [Category(**dict(row)) for row in rows]


def get_category_by_slug(slug: str) -> Optional[Category]:
    """Получить категорию по slug."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM categories WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        return Category(**dict(row)) if row else None


def create_category(name: str, slug: str, description: str = "", icon: str = "check-circle") -> bool:
    """Создать новую категорию."""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO categories (name, slug, description, icon) VALUES (?, ?, ?, ?)",
                (name, slug, description, icon)
            )
            conn.commit()
        return True
    except Exception:
        return False


# ====== ТЕМЫ ======

def get_topics_by_category(category_id: int) -> List[Topic]:
    """Получить все темы категории."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM topics WHERE category_id = ? ORDER BY order_num",
            (category_id,)
        )
        rows = cursor.fetchall()
        return [Topic(**dict(row)) for row in rows]


def get_topic_by_id(topic_id: int) -> Optional[Topic]:
    """Получить тему по ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
        row = cursor.fetchone()
        return Topic(**dict(row)) if row else None


def create_topic(category_id: int, title: str, content: str, order_num: int = 0) -> bool:
    """Создать новую тему."""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO topics (category_id, title, content, order_num) VALUES (?, ?, ?, ?)",
                (category_id, title, content, order_num)
            )
            conn.commit()
        return True
    except Exception:
        return False


# ====== ТЕСТЫ ======

def get_all_quizzes() -> List[Quiz]:
    """Получить все тесты."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM quizzes ORDER BY id")
        rows = cursor.fetchall()
        return [Quiz(**dict(row)) for row in rows]


def get_quizzes_by_category(category_id: int) -> List[Quiz]:
    """Получить тесты по категории."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM quizzes WHERE category_id = ? ORDER BY id",
            (category_id,)
        )
        rows = cursor.fetchall()
        return [Quiz(**dict(row)) for row in rows]


def get_quiz_by_id(quiz_id: int) -> Optional[Quiz]:
    """Получить тест по ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
        row = cursor.fetchone()
        return Quiz(**dict(row)) if row else None


def create_quiz(category_id: Optional[int], title: str, description: str = "") -> bool:
    """Создать новый тест."""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO quizzes (category_id, title, description) VALUES (?, ?, ?)",
                (category_id, title, description)
            )
            conn.commit()
        return True
    except Exception:
        return False


# ====== ВОПРОСЫ ======

def get_questions_by_quiz(quiz_id: int) -> List[Question]:
    """Получить все вопросы теста."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM questions WHERE quiz_id = ? ORDER BY order_num",
            (quiz_id,)
        )
        rows = cursor.fetchall()
        return [Question(**dict(row)) for row in rows]


def create_question(
    quiz_id: int,
    question_text: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    correct_option: str,
    explanation: str = "",
    order_num: int = 0,
    question_type: str = "single_choice"
) -> bool:
    """Создать новый вопрос."""
    if correct_option not in ("A", "B", "C", "D"):
        return False
    
    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO questions 
                   (quiz_id, question_text, option_a, option_b, option_c, option_d, 
                    correct_option, explanation, order_num, question_type) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (quiz_id, question_text, option_a, option_b, option_c, option_d,
                 correct_option, explanation, order_num, question_type)
            )
            conn.commit()
        return True
    except Exception:
        return False


# ====== РЕЗУЛЬТАТЫ ТЕСТОВ ======

def save_quiz_result(quiz_id: int, score: int, total: int, user_id: Optional[int] = None) -> str:
    """Сохранить результат теста."""
    result_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO quiz_results (id, quiz_id, score, total, created_at, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (result_id, quiz_id, score, total, created_at, user_id)
        )
        conn.commit()
    return result_id


def get_quiz_result_by_id(result_id: str) -> Optional[QuizResult]:
    """Получить результат теста по ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM quiz_results WHERE id = ?",
            (result_id,)
        )
        row = cursor.fetchone()
        return QuizResult(**dict(row)) if row else None


def get_quiz_results(quiz_id: int) -> List[QuizResult]:
    """Получить результаты теста."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM quiz_results WHERE quiz_id = ? ORDER BY created_at DESC",
            (quiz_id,)
        )
        rows = cursor.fetchall()
        return [QuizResult(**dict(row)) for row in rows]


# ====== СЛОВАРЬ ======

def get_all_glossary_terms() -> List[GlossaryTerm]:
    """Получить все термины словаря."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM glossary ORDER BY letter, term")
        rows = cursor.fetchall()
        return [GlossaryTerm(**dict(row)) for row in rows]


def search_glossary(query: str) -> List[GlossaryTerm]:
    """Поиск терминов в словаре."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM glossary WHERE term LIKE ? OR definition LIKE ?",
            (f"%{query}%", f"%{query}%")
        )
        rows = cursor.fetchall()
        return [GlossaryTerm(**dict(row)) for row in rows]


# ====== ОТЗЫВЫ ======

def create_feedback(name: str, message: str, email: str = "", rating: int = 0) -> str:
    """Создать отзыв."""
    feedback_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO feedback (id, name, email, message, rating, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (feedback_id, name, email, message, rating, created_at)
        )
        conn.commit()
    return feedback_id


def get_all_feedback() -> List[Feedback]:
    """Получить все отзывы."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [Feedback(**dict(row)) for row in rows]


# ====== ПОЛЬЗОВАТЕЛИ ======

def create_user(username: str, email: str, password: str) -> Tuple[bool, str]:
    """
    Создать нового пользователя.
    Возвращает (успех, сообщение).
    """
    if not validate_username(username):
        return False, "Недопустимое имя пользователя"
    
    if not validate_email(email):
        return False, "Недопустимый email"
    
    password_hash = hash_password(password)
    created_at = datetime.now().isoformat()
    
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, created_at)
            )
            
            # Создаём запись XP
            cursor = conn.execute("SELECT last_insert_rowid()")
            user_id = cursor.fetchone()[0]
            conn.execute(
                "INSERT INTO user_xp (user_id, xp, level) VALUES (?, 0, 1)",
                (user_id,)
            )
            conn.commit()
        return True, "Пользователь успешно создан"
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return False, "Пользователь с таким именем или email уже существует"
        return False, f"Ошибка при создании пользователя: {str(e)}"


def get_user_by_username(username: str) -> Optional[User]:
    """Получить пользователя по имени."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return User(**dict(row)) if row else None


def get_user_by_id(user_id: int) -> Optional[User]:
    """Получить пользователя по ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return User(**dict(row)) if row else None


# ====== ДОСТИЖЕНИЯ И ГЕЙМИФИКАЦИЯ ======

def add_xp(user_id: int, amount: int) -> int:
    """Добавить опыт пользователю. Возвращает новый уровень."""
    with get_db() as conn:
        # Получаем текущий XP и уровень
        cursor = conn.execute("SELECT xp, level FROM user_xp WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            # Создаём запись XP если нет
            conn.execute("INSERT INTO user_xp (user_id, xp, level) VALUES (?, ?, 1)", (user_id, amount))
            conn.commit()
            return 1
        
        current_xp, current_level = row
        new_xp = current_xp + amount
        new_level = current_level
        
        # Расчёт уровня: каждый уровень требует 100 * level XP
        xp_needed = 100 * current_level
        while new_xp >= xp_needed:
            new_xp -= xp_needed
            new_level += 1
            xp_needed = 100 * new_level
        
        conn.execute(
            "UPDATE user_xp SET xp = ?, level = ? WHERE user_id = ?",
            (new_xp, new_level, user_id)
        )
        conn.commit()
        return new_level


def check_achievements(user_id: int) -> List[Achievement]:
    """Проверить и выдать достижения пользователю."""
    earned = []
    
    with get_db() as conn:
        # Получаем статистику пользователя
        cursor = conn.execute("SELECT level FROM user_xp WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        user_level = row["level"] if row else 1
        
        cursor = conn.execute("SELECT COUNT(*) FROM quiz_results WHERE user_id = ?", (user_id,))
        quizzes_passed = cursor.fetchone()[0]
        
        # Получаем все достижения
        cursor = conn.execute("SELECT * FROM achievements")
        achievements = [Achievement(**dict(row)) for row in cursor.fetchall()]
        
        # Получаем уже полученные достижения
        cursor = conn.execute(
            "SELECT achievement_id FROM user_achievements WHERE user_id = ?",
            (user_id,)
        )
        earned_ids = {row["achievement_id"] for row in cursor.fetchall()}
        
        # Проверяем каждое достижение
        for achievement in achievements:
            if achievement.id in earned_ids:
                continue
            
            should_earn = False
            
            if achievement.requirement_type == "level":
                should_earn = user_level >= achievement.requirement_value
            elif achievement.requirement_type == "quizzes_passed":
                should_earn = quizzes_passed >= achievement.requirement_value
            
            if should_earn:
                conn.execute(
                    "INSERT INTO user_achievements (user_id, achievement_id, earned_at) VALUES (?, ?, ?)",
                    (user_id, achievement.id, datetime.now().isoformat())
                )
                earned.append(achievement)
        
        conn.commit()
    
    return earned


def get_user_achievements(user_id: int) -> List[UserAchievement]:
    """Получить достижения пользователя."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM user_achievements WHERE user_id = ? ORDER BY earned_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        return [UserAchievement(**dict(row)) for row in rows]


def get_platform_stats() -> dict:
    """Получить общую статистику платформы."""
    with get_db() as conn:
        # Количество категорий
        cursor = conn.execute("SELECT COUNT(*) FROM categories")
        categories = cursor.fetchone()[0]
        
        # Количество тем
        cursor = conn.execute("SELECT COUNT(*) FROM topics")
        topics = cursor.fetchone()[0]
        
        # Количество вопросов
        cursor = conn.execute("SELECT COUNT(*) FROM questions")
        questions = cursor.fetchone()[0]
        
        # Количество терминов в словаре
        cursor = conn.execute("SELECT COUNT(*) FROM glossary")
        glossary = cursor.fetchone()[0]
        
        return {
            "categories": categories,
            "topics": topics,
            "questions": questions,
            "glossary": glossary
        }


def get_user_stats(user_id: int) -> dict:
    """Получить статистику пользователя."""
    with get_db() as conn:
        # XP и уровень
        cursor = conn.execute("SELECT xp, level FROM user_xp WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        xp_data = {"xp": row["xp"], "level": row["level"]} if row else {"xp": 0, "level": 1}
        
        # Количество пройденных тестов
        cursor = conn.execute("SELECT COUNT(*) FROM quiz_results WHERE user_id = ?", (user_id,))
        quizzes_passed = cursor.fetchone()[0]
        
        # Средний результат
        cursor = conn.execute(
            "SELECT AVG(score * 100.0 / total) FROM quiz_results WHERE user_id = ?",
            (user_id,)
        )
        avg_score = cursor.fetchone()[0] or 0
        
        # Достижения
        cursor = conn.execute(
            "SELECT COUNT(*) FROM user_achievements WHERE user_id = ?",
            (user_id,)
        )
        achievements_count = cursor.fetchone()[0]
        
        return {
            "xp": xp_data["xp"],
            "level": xp_data["level"],
            "quizzes_passed": quizzes_passed,
            "avg_score": round(avg_score, 1),
            "achievements_count": achievements_count
        }
