from calendar import monthrange
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.auth import hash_password, require_parent
from app.database import get_db
from app.models import ChildProgress, LearningRecord, User, Word
from app.schemas import ChildCreate, ChildOut, ChildPasswordUpdate, DailyStat, WeakWordOut

router = APIRouter(prefix="/api/parent", tags=["parent"])


@router.get("/children", response_model=list[ChildOut])
def list_children(
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    children = db.query(User).filter(User.parent_id == parent.id).all()
    return children


@router.post("/children", response_model=ChildOut, status_code=status.HTTP_201_CREATED)
def create_child(
    data: ChildCreate,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このユーザー名は既に使用されています",
        )
    child = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        role="child",
        parent_id=parent.id,
    )
    db.add(child)
    db.flush()
    progress = ChildProgress(child_id=child.id)
    db.add(progress)
    db.commit()
    db.refresh(child)
    return child


@router.delete("/children/{child_id}")
def delete_child(
    child_id: int,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = db.query(User).filter(User.id == child_id, User.parent_id == parent.id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="子アカウントが見つかりません",
        )
    db.query(LearningRecord).filter(LearningRecord.child_id == child_id).delete()
    db.query(ChildProgress).filter(ChildProgress.child_id == child_id).delete()
    db.delete(child)
    db.commit()
    return {"detail": "子アカウントを削除しました"}


@router.put("/children/{child_id}/password")
def update_child_password(
    child_id: int,
    data: ChildPasswordUpdate,
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = db.query(User).filter(User.id == child_id, User.parent_id == parent.id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="子アカウントが見つかりません",
        )
    child.hashed_password = hash_password(data.password)
    db.commit()
    return {"detail": "パスワードを更新しました"}


@router.get("/children/{child_id}/stats", response_model=list[DailyStat])
def child_stats(
    child_id: int,
    year: int = Query(...),
    month: int = Query(...),
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = db.query(User).filter(User.id == child_id, User.parent_id == parent.id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="子アカウントが見つかりません",
        )

    jst_date = func.date(LearningRecord.answered_at, "+9 hours")

    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    rows = (
        db.query(
            jst_date.label("date"),
            # today
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "today",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == False,
                ), 1),
                else_=0,
            )).label("today_correct"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "today",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == True,
                ), 1),
                else_=0,
            )).label("today_hint"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "today",
                    LearningRecord.is_correct == False,
                ), 1),
                else_=0,
            )).label("today_incorrect"),
            # review
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "review",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == False,
                ), 1),
                else_=0,
            )).label("review_correct"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "review",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == True,
                ), 1),
                else_=0,
            )).label("review_hint"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "review",
                    LearningRecord.is_correct == False,
                ), 1),
                else_=0,
            )).label("review_incorrect"),
            # weak
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "weak",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == False,
                ), 1),
                else_=0,
            )).label("weak_correct"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "weak",
                    LearningRecord.is_correct == True,
                    LearningRecord.used_hint == True,
                ), 1),
                else_=0,
            )).label("weak_hint"),
            func.sum(case(
                (and_(
                    LearningRecord.session_type == "weak",
                    LearningRecord.is_correct == False,
                ), 1),
                else_=0,
            )).label("weak_incorrect"),
        )
        .filter(
            LearningRecord.child_id == child_id,
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
                today_correct=0,
                today_hint=0,
                today_incorrect=0,
                review_correct=0,
                review_hint=0,
                review_incorrect=0,
                weak_correct=0,
                weak_hint=0,
                weak_incorrect=0,
            ))
        current += timedelta(days=1)

    return result


@router.get("/children/{child_id}/weak-words", response_model=list[WeakWordOut])
def child_weak_words(
    child_id: int,
    sort_by: str = Query("accuracy"),
    order: str = Query("asc"),
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    child = db.query(User).filter(User.id == child_id, User.parent_id == parent.id).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="子アカウントが見つかりません",
        )

    return _get_weak_words(db, child_id, sort_by, order)


def _get_weak_words(db: Session, child_id: int, sort_by: str, order: str) -> list[WeakWordOut]:
    if order not in ("asc", "desc"):
        order = "asc"

    total = func.count(LearningRecord.id).label("total_attempts")
    correct_count = func.sum(case(
        (LearningRecord.is_correct == True, 1),
        else_=0,
    )).label("correct_count")
    hint_count = func.sum(case(
        (and_(LearningRecord.is_correct == True, LearningRecord.used_hint == True), 1),
        else_=0,
    )).label("hint_count")
    pure_correct = func.sum(case(
        (and_(LearningRecord.is_correct == True, LearningRecord.used_hint == False), 1),
        else_=0,
    ))

    rows = (
        db.query(
            Word.id,
            Word.english,
            Word.japanese,
            Word.english_katakana,
            total,
            correct_count,
            hint_count,
        )
        .join(LearningRecord, LearningRecord.word_id == Word.id)
        .filter(LearningRecord.child_id == child_id)
        .group_by(Word.id)
        .having(pure_correct * 1.0 / func.count(LearningRecord.id) < 0.9)
        .all()
    )

    result = []
    for row in rows:
        pure = row.correct_count - row.hint_count if row.correct_count and row.hint_count else (row.correct_count or 0)
        accuracy = round(pure / row.total_attempts, 3) if row.total_attempts else 0.0
        result.append(WeakWordOut(
            id=row.id,
            english=row.english,
            japanese=row.japanese,
            english_katakana=row.english_katakana,
            total_attempts=row.total_attempts,
            correct_count=row.correct_count or 0,
            hint_count=row.hint_count or 0,
            accuracy=accuracy,
        ))

    sort_key_map = {
        "accuracy": lambda x: x.accuracy,
        "total_attempts": lambda x: x.total_attempts,
        "english": lambda x: x.english.lower(),
        "japanese": lambda x: x.japanese,
    }
    key_fn = sort_key_map.get(sort_by, lambda x: x.accuracy)
    result.sort(key=key_fn, reverse=(order == "desc"))

    return result
