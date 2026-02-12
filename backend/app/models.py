from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "parent" or "child"
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    children = relationship(
        "User",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    parent = relationship(
        "User",
        back_populates="children",
        remote_side=[id],
        foreign_keys=[parent_id],
    )
    progress = relationship("ChildProgress", back_populates="child", uselist=False)
    learning_records = relationship("LearningRecord", back_populates="child")


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    english = Column(String, nullable=False)
    japanese = Column(String, nullable=False)
    english_katakana = Column(String, nullable=False)
    section = Column(Integer, index=True, nullable=False)


class ChildProgress(Base):
    __tablename__ = "child_progress"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    current_section = Column(Integer, default=1)
    last_section_date = Column(DateTime, nullable=True)

    child = relationship("User", back_populates="progress")


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    used_hint = Column(Boolean, default=False)
    answered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session_type = Column(String, nullable=False)  # "today" / "review" / "weak"

    child = relationship("User", back_populates="learning_records")
    word = relationship("Word")
