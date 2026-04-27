"""
Сервис управления пользователями
"""

from typing import Optional
from fastapi import Request

from app.services.data_service import get_user_by_id


def get_current_user_from_session(request: Request) -> Optional[dict]:
    """
    Получить текущего пользователя из сессии.
    Возвращает dict с данными пользователя или None.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    try:
        user = get_user_by_id(int(user_id))
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
    except (ValueError, TypeError):
        pass
    
    return None
