from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.auth import require_child
from app.database import get_db
from app.models import ChildProgress, LearningRecord, User, Word
from app.schemas import AnswerResult, AnswerSubmit, MenuStatus, QuizWord, WeakWordOut
from app.api.parent import _get_weak_words

router = APIRouter(prefix="/api/learning", tags=["learning"])


def _get_progress(db: Session, child_id: int) -> ChildProgress:
    progress = db.query(ChildProgress).filter(ChildProgress.child_id == child_id).first()
    if not progress:
        progress = ChildProgress(child_id=child_id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def _get_today_jst() -> datetime:
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc + timedelta(hours=9)
    return now_jst


@router.get("/today", response_model=list[QuizWord])
def today_words(
    child: User = Depends(require_child),
    db: Session = Depends(get_db),
):
    progress = _get_progress(db, child.id)
    today_jst = _get_today_jst().date()

    if progress.last_section_date is None:
        progress.last_section_date = datetime.now(timezone.utc)
        db.commit()
    else:
        last_date_jst = (progress.last_section_date + timedelta(hours=9)).date()
        if last_date_jst != today_jst:
            progress.current_section += 1
            progress.last_section_date = datetime.now(timezone.utc)
            db.commit()

    words = (
        db.query(Word)
        .filter(Word.section == progress.current_section)
        .order_by(func.random())
        .all()
    )
    return words


def _get_learned_word_ids(db: Session, child_id: int, period: str | None = None):
    query = (
        db.query(LearningRecord.word_id)
        .filter(LearningRecord.child_id == child_id)
        .distinct()
    )

    if period:
        now = datetime.now(timezone.utc)
        if period == "week":
            cutoff = now - timedelta(days=7)
            query = query.filter(LearningRecord.answered_at >= cutoff)
        elif period == "month":
            cutoff = now - timedelta(days=30)
            query = query.filter(LearningRecord.answered_at >= cutoff)
        elif period == "over_month":
            cutoff = now - timedelta(days=30)
            query = query.filter(LearningRecord.answered_at < cutoff)

    return [row[0] for row in query.all()]


@router.get("/review", response_model=list[QuizWord])
def review_words(
    period: str = Query("all"),
    child: User = Depends(require_child),
    db: Session = Depends(get_db),
):
    word_ids = _get_learned_word_ids(db, child.id, period if period != "all" else None)
    if not word_ids:
        return []
    words = (
        db.query(Word)
        .filter(Word.id.in_(word_ids))
        .order_by(func.random())
        .limit(10)
        .all()
    )
    return words


def _get_weak_word_ids(db: Session, child_id: int, period: str | None = None):
    total = func.count(LearningRecord.id).label("total")
    pure_correct = func.sum(case(
        (and_(LearningRecord.is_correct == True, LearningRecord.used_hint == False), 1),
        else_=0,
    ))

    query = (
        db.query(LearningRecord.word_id)
        .filter(LearningRecord.child_id == child_id)
    )

    if period:
        now = datetime.now(timezone.utc)
        if period == "month":
            cutoff = now - timedelta(days=30)
            query = query.filter(LearningRecord.answered_at >= cutoff)
        elif period == "over_month":
            cutoff = now - timedelta(days=30)
            query = query.filter(LearningRecord.answered_at < cutoff)

    rows = (
        query
        .group_by(LearningRecord.word_id)
        .having(pure_correct * 1.0 / func.count(LearningRecord.id) < 0.9)
        .all()
    )
    return [row[0] for row in rows]


@router.get("/weak", response_model=list[QuizWord])
def weak_words(
    period: str = Query("all"),
    child: User = Depends(require_child),
    db: Session = Depends(get_db),
):
    word_ids = _get_weak_word_ids(db, child.id, period if period != "all" else None)
    if not word_ids:
        return []
    words = (
        db.query(Word)
        .filter(Word.id.in_(word_ids))
        .order_by(func.random())
        .limit(10)
        .all()
    )
    return words


@router.post("/answer", response_model=AnswerResult)
def submit_answer(
    data: AnswerSubmit,
    child: User = Depends(require_child),
    db: Session = Depends(get_db),
):
    word = db.query(Word).filter(Word.id == data.word_id).first()
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="単語が見つかりません",
        )
    is_correct = data.answer.strip().lower() == word.english.lower()
    record = LearningRecord(
        child_id=child.id,
        word_id=data.word_id,
        is_correct=is_correct,
        used_hint=data.used_hint,
        answered_at=datetime.now(timezone.utc),
        session_type=data.session_type,
    )
    db.add(record)
    db.commit()
    return AnswerResult(
        is_correct=is_correct,
        correct_answer=word.english,
        english_katakana=word.english_katakana,
    )


@router.get("/menu-status", response_model=MenuStatus)
def menu_status(
    child: User = Depends(require_child),
    db: Session = Depends(get_db),
):
    progress = _get_progress(db, child.id)
    today_count = db.query(Word).filter(Word.section == progress.current_section).count()

    review_week = len(_get_learned_word_ids(db, child.id, "week"))
    review_month = len(_get_learned_word_ids(db, child.id, "month"))
    review_over_month = len(_get_learned_word_ids(db, child.id, "over_month"))
    review_all = len(_get_learned_word_ids(db, child.id, None))

    weak_month = len(_get_weak_word_ids(db, child.id, "month"))
    weak_over_month = len(_get_weak_word_ids(db, child.id, "over_month"))
    weak_all = len(_get_weak_word_ids(db, child.id, None))

    return MenuStatus(
        today=today_count,
        review_week=review_week,
        review_month=review_month,
        review_over_month=review_over_month,
        review_all=review_all,
        weak_month=weak_month,
        weak_over_month=weak_over_month,
        weak_all=weak_all,
    )


@router.get("/stats")
def my_stats(
    year: int = Query(...),
    month: int = Query(...),
    child: User = Depends(require_child),
    db: Session = Depends(get_db),
):
    from app.api.parent import child_stats as _parent_child_stats
    from types import SimpleNamespace

    # Reuse parent stats logic but with child's own ID
    from calendar import monthrange
    from datetime import date

    jst_date = func.date(LearningRecord.answered_at, "+9 hours")

    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    from app.schemas import DailyStat

    rows = (
        db.query(
            jst_date.label("date"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "today",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == False,
                ), 1), else_=0,
            )).label("today_correct"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "today",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == True,
                ), 1), else_=0,
            )).label("today_hint"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "today",
                    LearningRecord.is_correct == False,
                ), 1), else_=0,
            )).label("today_incorrect"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "review",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == False,
                ), 1), else_=0,
            )).label("review_correct"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "review",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == True,
                ), 1), else_=0,
            )).label("review_hint"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "review",
                    LearningRecord.is_correct == False,
                ), 1), else_=0,
            )).label("review_incorrect"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "weak",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == False,
                ), 1), else_=0,
            )).label("weak_correct"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "weak",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == True,
                ), 1), else_=0,
            )).label("weak_hint"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "weak",
                    LearningRecord.is_correct == False,
                ), 1), else_=0,
            )).label("weak_incorrect"),
        )
        .filter(
            LearningRecord.child_id == child.id,
            jst_date >= start_str,
            jst_date <= end_str,
        )
        .group_by(jst_date)
        .all()
    )

    stats_map = {}
    for row in rows:
        stats_map[row.date] = DailyStat(
            date=row.date,
            today_correct=row.today_correct or 0,
            today_hint=row.today_hint or 0,
            today_incorrect=row.today_incorrect or 0,
            review_correct=row.review_correct or 0,
            review_hint=row.review_hint or 0,
            review_incorrect=row.review_incorrect or 0,
            weak_correct=row.weak_correct or 0,
            weak_hint=row.weak_hint or 0,
            weak_incorrect=row.weak_incorrect or 0,
        )

    result = []
    current = start_date
    while current <= end_date:
        date_str = current.isoformat()
        if date_str in stats_map:
            result.append(stats_map[date_str])
        else:
            result.append(DailyStat(
                date=date_str,
                today_correct=0, today_hint=0, today_incorrect=0,
                review_correct=0, review_hint=0, review_incorrect=0,
                weak_correct=0, weak_hint=0, weak_incorrect=0,
            ))
        current += timedelta(days=1)

    return result


@router.get("/weak-words", response_model=list[WeakWordOut])
def my_weak_words(
    sort_by: str = Query("accuracy"),
    order: str = Query("asc"),
    child: User = Depends(require_child),
    db: Session = Depends(get_db),
):
    return _get_weak_words(db, child.id, sort_by, order)
