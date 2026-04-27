"""
Тесты для модулей аутентификации и валидации
"""

import pytest
from app.deps.auth import (
    hash_password, verify_password,
    validate_username, validate_email, validate_password,
    sanitize_input, generate_csrf_token
)


class TestPasswordHashing:
    """Тесты хеширования паролей."""
    
    def test_hash_password_returns_string(self):
        """Хеш пароля должен быть строкой."""
        result = hash_password("testpassword123")
        assert isinstance(result, str)
        assert ":" in result  # Формат salt:hash
    
    def test_hash_password_different_salts(self):
        """Одинаковые пароли должны иметь разные хеши из-за соли."""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Проверка правильного пароля должна возвращать True."""
        password = "SecurePass123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Проверка неправильного пароля должна возвращать False."""
        password = "SecurePass123"
        hashed = hash_password(password)
        assert verify_password("WrongPassword", hashed) is False


class TestUsernameValidation:
    """Тесты валидации имени пользователя."""
    
    def test_valid_username(self):
        """Валидные имена пользователей."""
        assert validate_username("john_doe") is True
        assert validate_username("user123") is True
        assert validate_username("test_user_1") is True
        assert validate_username("abc") is True  # Минимальная длина
        assert validate_username("a" * 32) is True  # Максимальная длина
    
    def test_invalid_username_too_short(self):
        """Слишком короткое имя."""
        assert validate_username("ab") is False
        assert validate_username("a") is False
        assert validate_username("") is False
    
    def test_invalid_username_too_long(self):
        """Слишком длинное имя."""
        assert validate_username("a" * 33) is False
    
    def test_invalid_username_special_chars(self):
        """Недопустимые специальные символы."""
        assert validate_username("user@name") is False
        assert validate_username("user-name") is False
        assert validate_username("user.name") is False
        assert validate_username("user name") is False


class TestEmailValidation:
    """Тесты валидации email."""
    
    def test_valid_emails(self):
        """Валидные email адреса."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.org") is True
        assert validate_email("user+tag@gmail.com") is True
        assert validate_email("test@sub.domain.com") is True
    
    def test_invalid_emails(self):
        """Невалидные email адреса."""
        assert validate_email("invalid") is False
        assert validate_email("@example.com") is False
        assert validate_email("test@") is False
        assert validate_email("test@.com") is False
        assert validate_email("") is False


class TestPasswordValidation:
    """Тесты валидации пароля."""
    
    def test_valid_password(self):
        """Валидный пароль."""
        is_valid, message = validate_password("SecurePass123")
        assert is_valid is True
        assert message == ""
    
    def test_password_too_short(self):
        """Пароль слишком короткий."""
        is_valid, message = validate_password("Short1!")
        assert is_valid is False
        assert "минимум 8 символов" in message
    
    def test_password_no_uppercase(self):
        """Пароль без заглавных букв."""
        is_valid, message = validate_password("lowercase123")
        assert is_valid is False
        assert "заглавную букву" in message
    
    def test_password_no_digit(self):
        """Пароль без цифр."""
        is_valid, message = validate_password("NoDigitsHere")
        assert is_valid is False
        assert "цифру" in message


class TestSanitizeInput:
    """Тесты санитизации входных данных."""
    
    def test_sanitize_normal_text(self):
        """Обычный текст не изменяется."""
        text = "Normal text without issues"
        assert sanitize_input(text) == text
    
    def test_sanitize_removes_html_tags(self):
        """HTML теги удаляются."""
        text = "<script>alert('xss')</script>Hello"
        result = sanitize_input(text)
        assert "<script>" not in result
        # Текст внутри тегов остаётся, сами теги удаляются
        assert "<" not in result or "script" not in result.split("<")[-1] if "<" in result else True
    
    def test_sanitize_limits_length(self):
        """Длина ограничивается max_length."""
        long_text = "a" * 2000
        result = sanitize_input(long_text, max_length=100)
        assert len(result) <= 100
    
    def test_sanitize_empty_string(self):
        """Пустая строка возвращается как есть."""
        assert sanitize_input("") == ""
        assert sanitize_input(None) == ""


class TestCSRFToken:
    """Тесты CSRF токенов."""
    
    def test_generate_csrf_token(self):
        """Генерация CSRF токена."""
        token = generate_csrf_token()
        assert isinstance(token, str)
        assert len(token) > 32  # Должен быть достаточно длинным
    
    def test_tokens_are_unique(self):
        """Каждый токен уникален."""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert token1 != token2
