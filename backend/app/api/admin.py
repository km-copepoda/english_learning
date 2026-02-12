import csv
import io

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.auth import require_parent
from app.database import get_db
from app.models import User, Word

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/import-words")
async def import_words(
    file: UploadFile = File(...),
    parent: User = Depends(require_parent),
    db: Session = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), fieldnames=["japanese", "english", "english_katakana", "section"],)

    imported = 0
    skipped = 0

    for row in reader:
        english = row["english"].strip()
        japanese = row["japanese"].strip()
        english_katakana = row["english_katakana"].strip()
        section = int(row["section"].strip())

        existing = (
            db.query(Word)
            .filter(Word.english == english, Word.japanese == japanese)
            .first()
        )
        if existing:
            skipped += 1
            continue

        word = Word(
            english=english,
            japanese=japanese,
            english_katakana=english_katakana,
            section=section,
        )
        db.add(word)
        imported += 1

    db.commit()
    return {"detail": f"{imported}件の単語を登録しました ({skipped}件は既登録のためスキップ)"}
