from datetime import datetime, timezone, timedelta

from app.models import ChildProgress, LearningRecord


class TestLearning:
    def test_today_words_initial(self, client, child_headers, sample_words):
        res = client.get("/api/learning/today", headers=child_headers)
        assert res.status_code == 200
        data = res.json()
        # Section 1 has 3 words (apple, banana, cat)
        assert len(data) == 3
        english_set = {w["english"] for w in data}
        assert english_set == {"apple", "banana", "cat"}

    def test_today_words_section_advance(self, client, child_headers, child_id, db, sample_words):
        progress = db.query(ChildProgress).filter(ChildProgress.child_id == child_id).first()
        # Set last_section_date to yesterday
        progress.last_section_date = datetime.now(timezone.utc) - timedelta(days=1)
        progress.current_section = 1
        db.commit()

        res = client.get("/api/learning/today", headers=child_headers)
        assert res.status_code == 200
        data = res.json()
        # Should advance to section 2 (dog, egg)
        assert len(data) == 2
        english_set = {w["english"] for w in data}
        assert english_set == {"dog", "egg"}

    def test_today_words_no_advance(self, client, child_headers, child_id, db, sample_words):
        progress = db.query(ChildProgress).filter(ChildProgress.child_id == child_id).first()
        # Set to today
        progress.last_section_date = datetime.now(timezone.utc)
        progress.current_section = 2
        db.commit()

        res = client.get("/api/learning/today", headers=child_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2  # Still section 2

    def test_review_words_empty(self, client, db, sample_words):
        # Create a new child with no records
        from app.models import User
        from app.auth import hash_password, create_access_token
        user = User(
            username="reviewempty",
            hashed_password=hash_password("pass"),
            role="child",
            parent_id=None,
        )
        db.add(user)
        db.flush()
        from app.models import ChildProgress
        db.add(ChildProgress(child_id=user.id))
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.username})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/learning/review?period=all", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_review_words_all(self, client, child_headers, child_id, db, sample_words):
        # Ensure there are learning records
        existing = db.query(LearningRecord).filter(LearningRecord.child_id == child_id).first()
        if not existing:
            db.add(LearningRecord(
                child_id=child_id, word_id=sample_words[0].id,
                is_correct=True, used_hint=False, session_type="today",
                answered_at=datetime.now(timezone.utc),
            ))
            db.commit()

        res = client.get("/api/learning/review?period=all", headers=child_headers)
        assert res.status_code == 200
        assert len(res.json()) > 0

    def test_weak_words_none_when_all_correct(self, client, db, sample_words):
        from app.models import User
        from app.auth import hash_password, create_access_token
        user = User(
            username="allcorrect",
            hashed_password=hash_password("pass"),
            role="child",
        )
        db.add(user)
        db.flush()
        from app.models import ChildProgress
        db.add(ChildProgress(child_id=user.id))
        # Add 10 correct (no hint) records for one word
        for _ in range(10):
            db.add(LearningRecord(
                child_id=user.id, word_id=sample_words[0].id,
                is_correct=True, used_hint=False, session_type="today",
                answered_at=datetime.now(timezone.utc),
            ))
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.username})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/learning/weak?period=all", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_weak_words_with_hint(self, client, db, sample_words):
        from app.models import User
        from app.auth import hash_password, create_access_token
        user = User(
            username="hintuser",
            hashed_password=hash_password("pass"),
            role="child",
        )
        db.add(user)
        db.flush()
        from app.models import ChildProgress
        db.add(ChildProgress(child_id=user.id))
        # 1 correct with hint, 1 incorrect = pure accuracy 0%
        db.add(LearningRecord(
            child_id=user.id, word_id=sample_words[0].id,
            is_correct=True, used_hint=True, session_type="today",
            answered_at=datetime.now(timezone.utc),
        ))
        db.add(LearningRecord(
            child_id=user.id, word_id=sample_words[0].id,
            is_correct=False, used_hint=False, session_type="today",
            answered_at=datetime.now(timezone.utc),
        ))
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.username})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/learning/weak?period=all", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) > 0

    def test_answer_correct(self, client, child_headers, sample_words):
        res = client.post("/api/learning/answer", headers=child_headers, json={
            "word_id": sample_words[0].id,
            "answer": "Apple",
            "session_type": "today",
            "used_hint": False,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["is_correct"] is True
        assert data["correct_answer"] == "apple"
        assert data["english_katakana"] == "アップル"

    def test_answer_correct_with_hint(self, client, child_headers, sample_words):
        res = client.post("/api/learning/answer", headers=child_headers, json={
            "word_id": sample_words[0].id,
            "answer": "Apple",
            "session_type": "today",
            "used_hint": True,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["is_correct"] is True

    def test_answer_incorrect(self, client, child_headers, sample_words):
        res = client.post("/api/learning/answer", headers=child_headers, json={
            "word_id": sample_words[0].id,
            "answer": "orange",
            "session_type": "today",
            "used_hint": False,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["is_correct"] is False
        assert data["correct_answer"] == "apple"

    def test_answer_nonexistent_word(self, client, child_headers):
        res = client.post("/api/learning/answer", headers=child_headers, json={
            "word_id": 99999,
            "answer": "test",
            "session_type": "today",
            "used_hint": False,
        })
        assert res.status_code == 404
        assert "単語が見つかりません" in res.json()["detail"]

    def test_menu_status(self, client, child_headers, sample_words):
        res = client.get("/api/learning/menu-status", headers=child_headers)
        assert res.status_code == 200
        data = res.json()
        assert "today" in data
        assert "review_week" in data
        assert "weak_all" in data

    def test_stats(self, client, child_headers, child_id, db, sample_words):
        from app.models import User
        from app.auth import hash_password, create_access_token
        user = User(
            username="statsuser",
            hashed_password=hash_password("pass"),
            role="child",
        )
        db.add(user)
        db.flush()
        from app.models import ChildProgress
        db.add(ChildProgress(child_id=user.id))

        # 2025-03-15 06:00 UTC = 2025-03-15 15:00 JST
        dt1 = datetime(2025, 3, 15, 6, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2025, 3, 31, 6, 0, 0, tzinfo=timezone.utc)
        records = [
            LearningRecord(child_id=user.id, word_id=sample_words[0].id,
                          is_correct=True, used_hint=False, session_type="today", answered_at=dt1),
            LearningRecord(child_id=user.id, word_id=sample_words[1].id,
                          is_correct=False, used_hint=False, session_type="today", answered_at=dt1),
            LearningRecord(child_id=user.id, word_id=sample_words[2].id,
                          is_correct=True, used_hint=True, session_type="review", answered_at=dt1),
            LearningRecord(child_id=user.id, word_id=sample_words[0].id,
                          is_correct=True, used_hint=False, session_type="review", answered_at=dt2),
        ]
        db.add_all(records)
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": user.username})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/learning/stats?year=2025&month=3", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 31  # March has 31 days

        mar15 = next(d for d in data if d["date"] == "2025-03-15")
        assert mar15["today_correct"] == 1
        assert mar15["today_incorrect"] == 1
        assert mar15["review_hint"] == 1

        mar31 = next(d for d in data if d["date"] == "2025-03-31")
        assert mar31["review_correct"] == 1

        # Other days should be 0
        mar01 = next(d for d in data if d["date"] == "2025-03-01")
        assert mar01["today_correct"] == 0

    def test_my_weak_words(self, client, child_headers):
        res = client.get("/api/learning/weak-words", headers=child_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_my_weak_words_sort(self, client, db, sample_words):
        from app.models import User
        from app.auth import hash_password, create_access_token
        user = User(
            username="sortuser",
            hashed_password=hash_password("pass"),
            role="child",
        )
        db.add(user)
        db.flush()
        from app.models import ChildProgress
        db.add(ChildProgress(child_id=user.id))

        # Create weak records for apple and banana
        for w in sample_words[:2]:
            db.add(LearningRecord(
                child_id=user.id, word_id=w.id,
                is_correct=False, used_hint=False, session_type="today",
                answered_at=datetime.now(timezone.utc),
            ))
        # Add more incorrect for banana
        db.add(LearningRecord(
            child_id=user.id, word_id=sample_words[1].id,
            is_correct=False, used_hint=False, session_type="today",
            answered_at=datetime.now(timezone.utc),
        ))
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": user.username})
        headers = {"Authorization": f"Bearer {token}"}

        # Sort by total_attempts desc
        res = client.get("/api/learning/weak-words?sort_by=total_attempts&order=desc", headers=headers)
        assert res.status_code == 200
        data = res.json()
        if len(data) >= 2:
            assert data[0]["total_attempts"] >= data[1]["total_attempts"]

        # Sort by english asc
        res = client.get("/api/learning/weak-words?sort_by=english&order=asc", headers=headers)
        assert res.status_code == 200
        data = res.json()
        if len(data) >= 2:
            assert data[0]["english"].lower() <= data[1]["english"].lower()

    def test_weak_words_accuracy_calc(self, client, db, sample_words):
        from app.models import User
        from app.auth import hash_password, create_access_token
        user = User(
            username="accuser",
            hashed_password=hash_password("pass"),
            role="child",
        )
        db.add(user)
        db.flush()
        from app.models import ChildProgress
        db.add(ChildProgress(child_id=user.id))

        # 1 correct (no hint) + 5 incorrect = 6 total, accuracy = 1/6 = 0.167
        db.add(LearningRecord(
            child_id=user.id, word_id=sample_words[0].id,
            is_correct=True, used_hint=False, session_type="today",
            answered_at=datetime.now(timezone.utc),
        ))
        for _ in range(5):
            db.add(LearningRecord(
                child_id=user.id, word_id=sample_words[0].id,
                is_correct=False, used_hint=False, session_type="today",
                answered_at=datetime.now(timezone.utc),
            ))
        db.commit()
        db.refresh(user)

        token = create_access_token(data={"sub": user.username})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/learning/weak-words", headers=headers)
        assert res.status_code == 200
        data = res.json()
        apple = next(w for w in data if w["english"] == "apple")
        assert apple["accuracy"] == 0.167
        assert apple["total_attempts"] == 6

    def test_learning_endpoints_require_child_role(self, client, parent_headers, sample_words):
        res = client.get("/api/learning/today", headers=parent_headers)
        assert res.status_code == 403

        res = client.get("/api/learning/review?period=all", headers=parent_headers)
        assert res.status_code == 403

        res = client.get("/api/learning/weak?period=all", headers=parent_headers)
        assert res.status_code == 403

        res = client.post("/api/learning/answer", headers=parent_headers, json={
            "word_id": 1, "answer": "test", "session_type": "today",
        })
        assert res.status_code == 403

    def test_menu_status_require_child(self, client, parent_headers):
        res = client.get("/api/learning/menu-status", headers=parent_headers)
        assert res.status_code == 403
