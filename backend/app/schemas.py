from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


# Auth
class ParentRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    email: str | None = None
    model_config = {"from_attributes": True}


# Child Management
class ChildCreate(BaseModel):
    username: str
    password: str


class ChildPasswordUpdate(BaseModel):
    password: str


class ChildOut(BaseModel):
    id: int
    username: str
    created_at: datetime
    model_config = {"from_attributes": True}


# Words
class WordOut(BaseModel):
    id: int
    english: str
    japanese: str
    english_katakana: str
    section: int
    model_config = {"from_attributes": True}


# Learning
class AnswerSubmit(BaseModel):
    word_id: int
    answer: str
    session_type: Literal["today", "review", "weak"]
    used_hint: bool = False


class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer: str
    english_katakana: str


class QuizWord(BaseModel):
    id: int
    english: str
    japanese: str
    english_katakana: str
    model_config = {"from_attributes": True}


class MenuStatus(BaseModel):
    today: int
    review_week: int
    review_month: int
    review_over_month: int
    review_all: int
    weak_month: int
    weak_over_month: int
    weak_all: int


# Stats
class DailyStat(BaseModel):
    date: str
    today_correct: int
    today_hint: int
    today_incorrect: int
    review_correct: int
    review_hint: int
    review_incorrect: int
    weak_correct: int
    weak_hint: int
    weak_incorrect: int


class WeakWordOut(BaseModel):
    id: int
    english: str
    japanese: str
    english_katakana: str
    total_attempts: int
    correct_count: int
    hint_count: int
    accuracy: float
    model_config = {"from_attributes": True}
