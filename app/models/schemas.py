"""
Модели данных TestLearn
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Category:
    id: int
    name: str
    slug: str
    description: str
    icon: str


@dataclass
class Topic:
    id: int
    category_id: int
    title: str
    content: str
    order_num: int


@dataclass
class Quiz:
    id: int
    category_id: Optional[int]
    title: str
    description: str


@dataclass
class Question:
    id: int
    quiz_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: str
    order_num: int
    question_type: str = "single_choice"


@dataclass
class QuizResult:
    id: str
    quiz_id: int
    score: int
    total: int
    created_at: str
    user_id: Optional[int] = None


@dataclass
class GlossaryTerm:
    id: int
    term: str
    definition: str
    letter: str


@dataclass
class Feedback:
    id: str
    name: str
    email: str
    message: str
    rating: int
    created_at: str


@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    created_at: str
    is_active: bool = True
    role: str = "user"


@dataclass
class Achievement:
    id: int
    name: str
    description: str
    icon: str
    requirement_type: str
    requirement_value: int


@dataclass
class UserAchievement:
    user_id: int
    achievement_id: int
    earned_at: str


@dataclass
class UserXP:
    user_id: int
    xp: int
    level: int
