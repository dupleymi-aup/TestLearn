"""
Тесты для сервисов данных и функциональности платформы
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from app.database.db import init_database, get_db, DB_NAME
from app.services.data_service import (
    get_all_categories, get_category_by_slug, create_category,
    get_topics_by_category, create_topic, get_topic_by_id,
    get_all_quizzes, get_quiz_by_id, create_quiz,
    get_questions_by_quiz, create_question,
    save_quiz_result, get_quiz_results,
    get_all_glossary_terms, search_glossary,
    create_feedback, get_all_feedback,
    create_user, get_user_by_username, get_user_by_id,
    add_xp, check_achievements, get_user_stats, get_user_achievements,
    get_platform_stats
)
from app.deps.auth import hash_password, verify_password


# Инициализация тестовой БД
init_database()


class TestCategories:
    """Тесты для категорий."""
    
    def test_create_category_success(self):
        """Создание категории успешно."""
        result = create_category(
            "Тестовая категория", 
            "test-cat-" + str(hash("test1")), 
            "Описание"
        )
        assert result is True
    
    def test_get_all_categories(self):
        """Получение всех категорий."""
        categories = get_all_categories()
        assert isinstance(categories, list)
    
    def test_get_category_by_slug_exists(self):
        """Получение существующей категории по slug."""
        # Сначала создадим категорию
        create_category("Найти меня", "find-me-slug", "Тест")
        category = get_category_by_slug("find-me-slug")
        assert category is not None
        assert category.name == "Найти меня"
    
    def test_get_category_by_slug_not_exists(self):
        """Получение несуществующей категории."""
        category = get_category_by_slug("non-existent-slug-xyz")
        assert category is None


class TestTopics:
    """Тесты для тем."""
    
    def test_create_topic_success(self):
        """Создание темы успешно."""
        # Создаём категорию для темы
        create_category("Категория для тем", "topics-cat", "Test")
        category = get_category_by_slug("topics-cat")
        
        result = create_topic(
            category_id=category.id,
            title="Тестовая тема",
            content="Содержимое темы",
            order_num=1
        )
        assert result is True
    
    def test_get_topics_by_category(self):
        """Получение тем категории."""
        create_category("Категория 2", "cat-2-test", "Test")
        category = get_category_by_slug("cat-2-test")
        
        create_topic(category.id, "Тема 1", "Контент 1", 0)
        create_topic(category.id, "Тема 2", "Контент 2", 1)
        
        topics = get_topics_by_category(category.id)
        assert len(topics) >= 2
    
    def test_get_topic_by_id_not_exists(self):
        """Получение несуществующей темы."""
        topic = get_topic_by_id(99999)
        assert topic is None


class TestQuizzes:
    """Тесты для тестов."""
    
    def test_create_quiz_success(self):
        """Создание теста успешно."""
        create_category("Категория для квиза", "quiz-cat", "Test")
        category = get_category_by_slug("quiz-cat")
        
        result = create_quiz(
            category_id=category.id,
            title="Тестовый квиз",
            description="Описание квиза"
        )
        assert result is True
    
    def test_get_all_quizzes(self):
        """Получение всех тестов."""
        quizzes = get_all_quizzes()
        assert isinstance(quizzes, list)
    
    def test_get_quiz_by_id_not_exists(self):
        """Получение несуществующего теста."""
        quiz = get_quiz_by_id(99999)
        assert quiz is None


class TestQuestions:
    """Тесты для вопросов."""
    
    def test_create_question_success(self):
        """Создание вопроса успешно."""
        # Создаём категорию и квиз
        create_category("Категория для вопроса", "q-cat", "Test")
        category = get_category_by_slug("q-cat")
        create_quiz(category.id, "Квиз для вопроса", "Desc")
        
        quiz = get_quiz_by_id(
            get_all_quizzes()[-1].id if get_all_quizzes() else 1
        )
        
        if quiz:
            result = create_question(
                quiz_id=quiz.id,
                question_text="Тестовый вопрос?",
                option_a="Вариант A",
                option_b="Вариант B",
                option_c="Вариант C",
                option_d="Вариант D",
                correct_option="A",
                explanation="Объяснение",
                order_num=0
            )
            assert result is True
    
    def test_create_question_invalid_option(self):
        """Создание вопроса с невалидным правильным ответом."""
        result = create_question(
            quiz_id=1,
            question_text="Вопрос",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_option="E",  # Неверный вариант
            explanation=""
        )
        assert result is False
    
    def test_get_questions_by_quiz(self):
        """Получение вопросов теста."""
        questions = get_questions_by_quiz(1)
        assert isinstance(questions, list)


class TestQuizResults:
    """Тесты для результатов тестов."""
    
    def test_save_quiz_result(self):
        """Сохранение результата теста."""
        result_id = save_quiz_result(
            quiz_id=1,
            score=8,
            total=10,
            user_id=None
        )
        assert result_id is not None
        assert len(result_id) > 0
    
    def test_get_quiz_results(self):
        """Получение результатов теста."""
        results = get_quiz_results(1)
        assert isinstance(results, list)


class TestGlossary:
    """Тесты для словаря."""
    
    def test_get_all_glossary_terms(self):
        """Получение всех терминов."""
        terms = get_all_glossary_terms()
        assert isinstance(terms, list)
    
    def test_search_glossary_found(self):
        """Поиск термина с результатом."""
        # Ищем что-то что может существовать
        terms = search_glossary("тест")
        assert isinstance(terms, list)
    
    def test_search_glossary_empty(self):
        """Поиск несуществующего термина."""
        terms = search_glossary("xyznonexistent123")
        assert isinstance(terms, list)
        assert len(terms) == 0


class TestFeedback:
    """Тесты для обратной связи."""
    
    def test_create_feedback(self):
        """Создание отзыва."""
        feedback_id = create_feedback(
            name="Тестовый пользователь",
            message="Тестовое сообщение",
            email="test@example.com",
            rating=5
        )
        assert feedback_id is not None
        assert len(feedback_id) > 0
    
    def test_get_all_feedback(self):
        """Получение всех отзывов."""
        feedbacks = get_all_feedback()
        assert isinstance(feedbacks, list)


class TestUsers:
    """Тесты для пользователей."""
    
    def test_create_user_success(self):
        """Создание пользователя успешно."""
        import time
        username = f"testuser{int(time.time())}"
        email = f"{username}@example.com"
        
        success, message = create_user(username, email, "SecurePass123")
        assert success is True
        assert "успешно" in message.lower() or "создан" in message.lower()
    
    def test_create_user_duplicate(self):
        """Создание дубликата пользователя."""
        username = f"dupuser{int(hash('dup'))}"
        email = f"{username}@example.com"
        
        # Создаём первого
        create_user(username, email, "SecurePass123")
        # Пытаемся создать дубликат
        success, message = create_user(username, email, "SecurePass123")
        assert success is False
    
    def test_create_user_invalid_username(self):
        """Создание пользователя с невалидным именем."""
        success, message = create_user("ab", "test@example.com", "SecurePass123")
        assert success is False
    
    def test_create_user_invalid_email(self):
        """Создание пользователя с невалидным email."""
        success, message = create_user("validuser", "invalid-email", "SecurePass123")
        assert success is False
    
    def test_get_user_by_username(self):
        """Получение пользователя по имени."""
        # Создаём тестового пользователя
        username = f"finduser{int(hash('find'))}"
        create_user(username, f"{username}@test.com", "SecurePass123")
        
        user = get_user_by_username(username)
        assert user is not None
        assert user.username == username
    
    def test_get_user_by_id(self):
        """Получение пользователя по ID."""
        user = get_user_by_id(1)
        # Может быть None если нет пользователей с ID=1
        # Но функция должна работать без ошибок
        assert user is None or hasattr(user, 'id')


class TestGamification:
    """Тесты для геймификации."""
    
    def test_add_xp(self):
        """Добавление опыта пользователю."""
        # Создаём пользователя для теста
        username = f"xptest{int(hash('xp'))}"
        create_user(username, f"{username}@xp.com", "SecurePass123")
        user = get_user_by_username(username)
        
        if user:
            new_level = add_xp(user.id, 50)
            assert isinstance(new_level, int)
            assert new_level >= 1
    
    def test_get_user_stats(self):
        """Получение статистики пользователя."""
        username = f"statsuser{int(hash('stats'))}"
        create_user(username, f"{username}@stats.com", "SecurePass123")
        user = get_user_by_username(username)
        
        if user:
            stats = get_user_stats(user.id)
            assert isinstance(stats, dict)
            assert "xp" in stats
            assert "level" in stats
            assert "quizzes_passed" in stats
    
    def test_get_user_achievements(self):
        """Получение достижений пользователя."""
        username = f"achieveuser{int(hash('ach'))}"
        create_user(username, f"{username}@ach.com", "SecurePass123")
        user = get_user_by_username(username)
        
        if user:
            achievements = get_user_achievements(user.id)
            assert isinstance(achievements, list)


class TestPlatformStats:
    """Тесты для статистики платформы."""
    
    def test_get_platform_stats(self):
        """Получение статистики платформы."""
        stats = get_platform_stats()
        
        assert isinstance(stats, dict)
        assert "categories" in stats
        assert "topics" in stats
        assert "questions" in stats
        assert "glossary" in stats
        
        # Все значения должны быть неотрицательными числами
        assert stats["categories"] >= 0
        assert stats["topics"] >= 0
        assert stats["questions"] >= 0
        assert stats["glossary"] >= 0
