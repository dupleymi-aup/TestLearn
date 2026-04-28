"""
База данных TestLearn - конфигурация и утилиты
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

# Database configuration from environment variable (for testing)
DB_NAME = os.getenv("TESTLEARN_DB", "testlearn.db")


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Контекстный менеджер для подключения к БД."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Инициализация таблиц БД."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Таблица категорий (виды тестирования)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL UNIQUE,
                description TEXT,
                icon TEXT DEFAULT 'check-circle'
            )
        """)

        # Таблица тем/материалов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                order_num INTEGER DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)

        # Таблица тестов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                time_limit INTEGER DEFAULT 600,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        """)

        # Таблица вопросов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option TEXT NOT NULL,
                explanation TEXT DEFAULT '',
                order_num INTEGER DEFAULT 0,
                question_type TEXT DEFAULT 'single_choice',
                expected_answer TEXT,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            )
        """)

        # Таблица для вопросов на сопоставление (matching)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matching_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                left_item TEXT NOT NULL,
                right_item TEXT NOT NULL,
                pair_order INTEGER DEFAULT 0,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            )
        """)

        # Таблица для вопросов на упорядочивание (ordering)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ordering_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                item_text TEXT NOT NULL,
                correct_order INTEGER NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            )
        """)

        # Таблица результатов тестов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id TEXT PRIMARY KEY,
                quiz_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            )
        """)

        # Таблица словаря терминов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS glossary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL UNIQUE,
                definition TEXT NOT NULL,
                letter TEXT NOT NULL
            )
        """)

        # Таблица отзывов/комментариев
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT DEFAULT '',
                message TEXT NOT NULL,
                rating INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        # Таблица прогресса пользователя (по сессии)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL UNIQUE,
                topics_read INTEGER DEFAULT 0,
                quizzes_passed INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                last_visit TEXT,
                UNIQUE(session_id)
            )
        """)

        # Таблица прочитанных тем (детальное отслеживание)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS read_topics (
                session_id TEXT NOT NULL,
                topic_id INTEGER NOT NULL,
                read_at TEXT NOT NULL,
                PRIMARY KEY (session_id, topic_id)
            )
        """)

        # Таблица закладок
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                session_id TEXT NOT NULL,
                topic_id INTEGER NOT NULL,
                bookmarked_at TEXT NOT NULL,
                PRIMARY KEY (session_id, topic_id),
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        """)

        # Таблица сессий администратора
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                expires TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Таблица пользователей (для регистрации)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                role TEXT DEFAULT 'user'
            )
        """)

        # Таблица достижений (геймификация)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                icon TEXT DEFAULT 'trophy',
                requirement_type TEXT NOT NULL,
                requirement_value INTEGER NOT NULL
            )
        """)

        # Таблица пользовательских достижений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                earned_at TEXT NOT NULL,
                PRIMARY KEY (user_id, achievement_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
            )
        """)

        # Таблица очков опыта (XP)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_xp (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
